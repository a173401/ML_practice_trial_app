import pytest
from lib.app.settings import Settings
from sqlmodel import Field, SQLModel, create_engine

@pytest.fixture(scope="session")
def settings():
    return Settings()

@pytest.fixture(scope="module", autouse=True)
def database_engine(settings: Settings):
    engine = create_engine("sqlite:///:memory:")  # Use an in-memory SQLite database for testing
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield engine