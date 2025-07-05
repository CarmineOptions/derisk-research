import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from app.crud.base import DBConnectorAsync


class MockModel(BaseModel):
    """Mock model for testing purposes"""

    id: uuid.UUID
    name: str

    class Config:
        from_attributes = True


@pytest.fixture
def mock_db_url() -> str:
    """Mock database URL for testing"""
    return "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def db_connector(mock_db_url: str) -> DBConnectorAsync:
    """Create DBConnectorAsync instance with mocked dependencies"""
    with patch("app.crud.base.create_async_engine") as mock_engine, patch(
        "app.crud.base.async_sessionmaker"
    ) as mock_sessionmaker:

        connector = DBConnectorAsync(mock_db_url)
        connector.engine = mock_engine.return_value
        connector.session_maker = mock_sessionmaker.return_value
        return connector


@pytest.fixture
def mock_session():
    """Mock async session"""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.refresh = AsyncMock()
    session.merge = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def sample_model_instance() -> MockModel:
    """Sample model instance for testing"""
    return MockModel(id=uuid.uuid4(), name="test_object")


class TestDBConnectorAsync:
    """Test suite for DBConnectorAsync class"""

    def test_init(self, mock_db_url: str):
        """Test DBConnectorAsync initialization"""
        with patch("app.crud.base.create_async_engine") as mock_engine, patch(
            "app.crud.base.async_sessionmaker"
        ) as mock_sessionmaker:

            connector = DBConnectorAsync(mock_db_url)

            mock_engine.assert_called_once_with(mock_db_url)
            mock_sessionmaker.assert_called_once_with(mock_engine.return_value)
            assert connector.engine == mock_engine.return_value
            assert connector.session_maker == mock_sessionmaker.return_value

    @pytest.mark.asyncio
    async def test_session_context_manager_success(
        self, db_connector: DBConnectorAsync, mock_session
    ):
        """Test successful session context manager"""
        db_connector.session_maker.return_value = mock_session

        async with db_connector.session() as session:
            assert session == mock_session

        mock_session.close.assert_called_once()
        mock_session.rollback.assert_not_called()

    @pytest.mark.asyncio
    async def test_session_context_manager_with_sqlalchemy_error(
        self, db_connector: DBConnectorAsync, mock_session
    ):
        """Test session context manager with SQLAlchemy error"""
        db_connector.session_maker.return_value = mock_session

        with pytest.raises(
            Exception, match="Error occurred while processing database operation"
        ):
            async with db_connector.session() as session:
                raise SQLAlchemyError("Test error")

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_write_to_db_success(
        self,
        db_connector: DBConnectorAsync,
        mock_session,
        sample_model_instance: MockModel,
    ):
        """Test successful write_to_db operation"""
        db_connector.session_maker.return_value = mock_session
        mock_session.merge.return_value = sample_model_instance

        result = await db_connector.write_to_db(sample_model_instance)

        mock_session.merge.assert_called_once_with(sample_model_instance)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(sample_model_instance)
        mock_session.close.assert_called_once()
        assert result == sample_model_instance

    @pytest.mark.asyncio
    async def test_get_object_success(
        self,
        db_connector: DBConnectorAsync,
        mock_session,
        sample_model_instance: MockModel,
    ):
        """Test successful get_object operation"""
        db_connector.session_maker.return_value = mock_session
        mock_session.get.return_value = sample_model_instance
        test_id = sample_model_instance.id

        result = await db_connector.get_object(MockModel, test_id)

        mock_session.get.assert_called_once_with(MockModel, test_id)
        mock_session.close.assert_called_once()
        assert result == sample_model_instance

    @pytest.mark.asyncio
    async def test_get_object_not_found(
        self, db_connector: DBConnectorAsync, mock_session
    ):
        """Test get_object when object not found"""
        db_connector.session_maker.return_value = mock_session
        mock_session.get.return_value = None
        test_id = uuid.uuid4()

        result = await db_connector.get_object(MockModel, test_id)

        mock_session.get.assert_called_once_with(MockModel, test_id)
        mock_session.close.assert_called_once()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_objects_success(
        self,
        db_connector: DBConnectorAsync,
        mock_session,
        sample_model_instance: MockModel,
    ):
        """Test successful get_objects operation"""
        db_connector.session_maker.return_value = mock_session

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_model_instance]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        with patch("app.crud.base.select") as mock_select:
            mock_stmt = MagicMock()
            mock_select.return_value.filter_by.return_value = mock_stmt

            result = await db_connector.get_objects(MockModel, name="test")

            mock_select.assert_called_once_with(MockModel)
            mock_select.return_value.filter_by.assert_called_once_with(name="test")
            mock_session.execute.assert_called_once_with(mock_stmt)
            mock_result.scalars.assert_called_once()
            mock_scalars.all.assert_called_once()
            mock_session.close.assert_called_once()
            assert result == [sample_model_instance]

    @pytest.mark.asyncio
    async def test_get_objects_empty_result(
        self, db_connector: DBConnectorAsync, mock_session
    ):
        """Test get_objects with empty result"""
        db_connector.session_maker.return_value = mock_session

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        with patch("app.crud.base.select") as mock_select:
            mock_stmt = MagicMock()
            mock_select.return_value.filter_by.return_value = mock_stmt

            result = await db_connector.get_objects(MockModel)

            mock_session.close.assert_called_once()
            assert result == []

    @pytest.mark.asyncio
    async def test_get_object_by_field_success(
        self,
        db_connector: DBConnectorAsync,
        mock_session,
        sample_model_instance: MockModel,
    ):
        """Test successful get_object_by_field operation"""
        db_connector.session_maker.return_value = mock_session

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_model_instance
        mock_session.execute.return_value = mock_result

        with patch("app.crud.base.select") as mock_select:
            mock_field_attr = MagicMock()
            setattr(MockModel, "name", mock_field_attr)
            mock_where_stmt = MagicMock()
            mock_select.return_value.where.return_value = mock_where_stmt

            result = await db_connector.get_object_by_field(
                MockModel, "name", "test_value"
            )

            mock_select.assert_called_once_with(MockModel)
            mock_session.execute.assert_called_once_with(mock_where_stmt)
            mock_result.scalar_one_or_none.assert_called_once()
            mock_session.close.assert_called_once()
            assert result == sample_model_instance

    @pytest.mark.asyncio
    async def test_get_object_by_field_not_found(
        self, db_connector: DBConnectorAsync, mock_session
    ):
        """Test get_object_by_field when object not found"""
        db_connector.session_maker.return_value = mock_session

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with patch("app.crud.base.select") as mock_select:
            mock_field_attr = MagicMock()
            setattr(MockModel, "name", mock_field_attr)
            mock_where_stmt = MagicMock()
            mock_select.return_value.where.return_value = mock_where_stmt

            result = await db_connector.get_object_by_field(
                MockModel, "name", "nonexistent"
            )

            mock_session.close.assert_called_once()
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_object_by_id_success(
        self,
        db_connector: DBConnectorAsync,
        mock_session,
        sample_model_instance: MockModel,
    ):
        """Test successful delete_object_by_id operation"""
        db_connector.session_maker.return_value = mock_session
        mock_session.get.return_value = sample_model_instance
        test_id = sample_model_instance.id

        await db_connector.delete_object_by_id(MockModel, test_id)

        mock_session.get.assert_called_once_with(MockModel, test_id)
        mock_session.delete.assert_called_once_with(sample_model_instance)
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_object_by_id_not_found(
        self, db_connector: DBConnectorAsync, mock_session
    ):
        """Test delete_object_by_id when object not found (idempotent)"""
        db_connector.session_maker.return_value = mock_session
        mock_session.get.return_value = None
        test_id = uuid.uuid4()

        await db_connector.delete_object_by_id(MockModel, test_id)

        mock_session.get.assert_called_once_with(MockModel, test_id)
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_object_success(
        self,
        db_connector: DBConnectorAsync,
        mock_session,
        sample_model_instance: MockModel,
    ):
        """Test successful delete_object operation"""
        db_connector.session_maker.return_value = mock_session

        await db_connector.delete_object(sample_model_instance)

        mock_session.delete.assert_called_once_with(sample_model_instance)
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_write_to_db_with_sqlalchemy_error(
        self,
        db_connector: DBConnectorAsync,
        mock_session,
        sample_model_instance: MockModel,
    ):
        """Test write_to_db with SQLAlchemy error"""
        db_connector.session_maker.return_value = mock_session
        mock_session.commit.side_effect = SQLAlchemyError("Database error")

        with pytest.raises(
            Exception, match="Error occurred while processing database operation"
        ):
            await db_connector.write_to_db(sample_model_instance)

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_object_with_sqlalchemy_error(
        self, db_connector: DBConnectorAsync, mock_session
    ):
        """Test get_object with SQLAlchemy error"""
        db_connector.session_maker.return_value = mock_session
        mock_session.get.side_effect = SQLAlchemyError("Database error")
        test_id = uuid.uuid4()

        with pytest.raises(
            Exception, match="Error occurred while processing database operation"
        ):
            await db_connector.get_object(MockModel, test_id)

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_object_with_sqlalchemy_error(
        self,
        db_connector: DBConnectorAsync,
        mock_session,
        sample_model_instance: MockModel,
    ):
        """Test delete_object with SQLAlchemy error"""
        db_connector.session_maker.return_value = mock_session
        mock_session.delete.side_effect = SQLAlchemyError("Database error")

        with pytest.raises(
            Exception, match="Error occurred while processing database operation"
        ):
            await db_connector.delete_object(sample_model_instance)

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
