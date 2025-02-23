from lib.database.database_models import UserSchema, AccountSchema
from lib.models.user_account_dto import UserRole
from sqlmodel import Session, select
import pytest

@pytest.mark.unit
def test_create_user(database_engine):
    user = UserSchema(username="testuser", email="test@example.com", hashed_password="$2b$12$examplehash", 
                      role=UserRole.ADMIN)
    with Session(database_engine) as session:
        session.add(user)
        session.commit()
        assert user.id is not None
    
@pytest.mark.unit
def test_read_user(database_engine):
    with Session(database_engine) as session:
        statement = select(UserSchema).where(UserSchema.username == "testuser")
        user = session.exec(statement).first()
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.ADMIN

@pytest.mark.unit
def test_modify_user(database_engine):
    with Session(database_engine) as session:
        statement = select(UserSchema).where(UserSchema.username == "testuser")
        user = session.exec(statement).first()
        user.email = "newemail@example.com"
        session.add(user)
        session.commit()
        session.refresh(user)
        assert user.email == "newemail@example.com"