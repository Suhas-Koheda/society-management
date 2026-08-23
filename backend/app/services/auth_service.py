from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User

_DUMMY_HASH = hash_password("dummy-password-for-timing-equalization")


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


def normalize_email(email: str) -> str:
    return email.strip().lower()


def register_user(db: Session, name: str, email: str, password: str) -> User:
    email = normalize_email(email)

    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise EmailAlreadyRegisteredError(email)

    user = User(
        name=name.strip(),
        email=email,
        password_hash=hash_password(password),
        role="resident",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    email = normalize_email(email)
    user = db.scalar(select(User).where(User.email == email))

    if user is None:
        verify_password(password, _DUMMY_HASH)
        raise InvalidCredentialsError

    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError

    return user


def create_access_token_for_user(user: User) -> str:
    return create_access_token(subject=user.id)
