from lib.database.database_models import UserSchema, AccountSchema
from lib.models.user_account_dto import UserRole
from sqlmodel import Session, select


def test_create_account(database_engine):
    # Create a user
    user = UserSchema(username="testuser", email="test@example.com", hashed_password="$2b$12$examplehash", 
                      role=UserRole.ADMIN)
    account = AccountSchema(user=user, balance=100.0)
    with Session(database_engine) as session:
        session.add(account)
        session.commit()
        session.refresh(account)
        session.refresh(user)
        assert account.id is not None
        assert account.user.id == user.id
    