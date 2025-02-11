import pytest
from app import Settings
from sqlmodel import Field, SQLModel, create_engine

@pytest.fixture(scope="session")
def settings():
    return Settings()

@pytest.fixture(scope="module")
def database_engine(settings: Settings):
    # Setup code to create a database session
    engine = create_engine(
        f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}/{settings.postgres_db}",
    )
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield engine