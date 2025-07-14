import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from data_handler.handlers.loan_states.vesu.events import VesuLoanEntity
from data_handler.db.models.liquidable_debt import HealthRatioLevel


@pytest.fixture
def vesu_entity():
    """Create VesuLoanEntity instance for testing"""
    with patch("data_handler.handlers.loan_states.vesu.events.StarknetClient"), patch(
        "data_handler.handlers.loan_states.vesu.events.DBConnector"
    ):
        entity = VesuLoanEntity()
        entity.session = AsyncMock()
        return entity


@pytest.fixture
def mock_session():
    """Mock database session"""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_vesu_position():
    """Mock VesuPosition object"""
    position = MagicMock()
    position.pool_id = "456"
    position.collateral_asset = "789"
    position.debt_asset = "101112"
    position.get.return_value = 1000000


class TestVesuLoanEntity:

    @pytest.mark.asyncio
    async def test_save_health_ratio_level(self, vesu_entity, mock_session):
        """Test saving health ratio level to database"""
        result = await vesu_entity.save_health_ratio_level(
            session=mock_session,
            timestamp=1234567890,
            user_id="0x123",
            value=Decimal("1.5"),
            protocol_id="vesu",
        )

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

        added_record = mock_session.add.call_args[0][0]
        assert isinstance(added_record, HealthRatioLevel)
        assert added_record.timestamp == 1234567890
        assert added_record.user_id == "0x123"
        assert added_record.value == Decimal("1.5")
        assert added_record.protocol_id == "vesu"

    @pytest.mark.asyncio
    async def test_calculate_health_factor_with_session(
        self, vesu_entity, mock_session, mock_vesu_position
    ):
        """Test calculate_health_factor saves to database when session provided"""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_vesu_position]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        vesu_entity.session.execute = AsyncMock(return_value=mock_result)

        with patch.object(
            vesu_entity, "_get_position_data"
        ) as mock_position, patch.object(
            vesu_entity, "_get_collateral_value"
        ) as mock_collateral, patch.object(
            vesu_entity, "_get_asset_config"
        ) as mock_asset_config, patch.object(
            vesu_entity, "_calculate_debt"
        ) as mock_debt, patch.object(
            vesu_entity, "get_ltv_config"
        ) as mock_ltv, patch.object(
            vesu_entity, "_get_token_decimals"
        ) as mock_decimals, patch.object(
            vesu_entity, "fetch_token_price"
        ) as mock_price, patch.object(
            vesu_entity, "save_health_ratio_level"
        ) as mock_save:

            mock_position.return_value = (
                100,
                0,
                200,
                0,
            )
            mock_collateral.return_value = Decimal("1000")
            mock_asset_config.return_value = [0] * 16
            mock_debt.return_value = Decimal("500")
            mock_ltv.return_value = (Decimal("80"),)
            mock_decimals.return_value = Decimal("1000000")
            mock_price.return_value = Decimal("2000")

            result = await vesu_entity.calculate_health_factor(
                123, session=mock_session
            )

            mock_save.assert_called_once_with(
                session=mock_session,
                timestamp=1000000,
                user_id="123",
                value=result["0x1c8"],
                protocol_id=456,
            )

    @pytest.mark.asyncio
    async def test_calculate_health_factor_without_session(self, vesu_entity):
        """Test calculate_health_factor doesn't save when no session provided"""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        vesu_entity.session.execute = AsyncMock(return_value=mock_result)

        with patch.object(vesu_entity, "save_health_ratio_level") as mock_save:
            result = await vesu_entity.calculate_health_factor(123)

            mock_save.assert_not_called()
            assert result == {}
