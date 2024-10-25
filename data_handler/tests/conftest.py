import pytest
from db.crud import DBConnector
from db.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="session")
def mock_db_url():
    return "sqlite:///:memory:"

@pytest.fixture(scope="function")
def mock_session(mock_db_url):
    engine = create_engine(mock_db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    
    yield session
    
    session.close()

@pytest.fixture(scope="function")
def mock_db_connector(mock_session):
    return DBConnector(db_url="sqlite:///:memory:")
