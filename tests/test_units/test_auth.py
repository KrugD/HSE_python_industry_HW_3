import pytest
from fastapi import HTTPException
from app.auth import create_access_token, get_current_user, check_admin, decode_access_token
from app.models import User

@pytest.fixture
def mock_user_admin():
    return User(username="admin", role="admin")

@pytest.fixture
def mock_user_regular():
    return User(username="user", role="user")

@pytest.mark.asyncio
async def test_valid_token_verification(mocker):
    mock_db = mocker.MagicMock()
    mock_user = User(username="test")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    token = create_access_token({"sub": "test"})
    user = await get_current_user(
        credentials=mocker.MagicMock(credentials=token),
        db=mock_db
    )
    assert user.username == "test"

def test_admin_access(mock_user_admin):
    check_admin(mock_user_admin)

def test_non_admin_access(mock_user_regular):
    with pytest.raises(HTTPException) as exc:
        check_admin(mock_user_regular)
    assert exc.value.status_code == 403

def test_decode_access_token_valid():
    token = create_access_token({"sub": "test_user"})
    payload = decode_access_token(token)
    assert payload["sub"] == "test_user"

def test_decode_access_token_invalid():
    with pytest.raises(HTTPException):
        decode_access_token("invalid.token.here")

