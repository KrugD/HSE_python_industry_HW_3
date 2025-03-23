import pytest
from datetime import timedelta
from app.auth import create_access_token
from app.utils import (
    generate_short_code, 
    get_password_hash, 
    verify_password, 
    generate_api_token, 
    decode_access_token
)
import time

def test_generate_short_code():
    code = generate_short_code()
    assert len(code) == 6
    assert code.isalnum()

def test_password_hashing():
    password = "secret"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)

def test_generate_api_token():
    token = generate_api_token()
    assert len(token) == 43  # 32 bytes in urlsafe base64

def test_decode_valid_token():
    token = create_access_token({"sub": "test"})
    payload = decode_access_token(token)
    assert payload["sub"] == "test"

def test_decode_invalid_token():
    # Проверка правильного возврата None для недопустимого токена
    assert decode_access_token("invalid.token.here") is None

def test_create_access_token_expiry():
    token = create_access_token(
        data={"sub": "test"},
        expires_delta=timedelta(minutes=5)
    )
    payload = decode_access_token(token)
    assert payload.get("exp") is not None

def test_short_code_uniqueness():
    codes = {generate_short_code() for _ in range(100)}
    assert len(codes) == 100  # Проверка уникальности

def test_jwt_expiration():
    token = create_access_token({"sub": "test"}, expires_delta=timedelta(seconds=1))
    payload = decode_access_token(token)
    assert payload["sub"] == "test"
    time.sleep(2)
    # После истечения срока действия токена, decode_access_token должен вернуть None
    assert decode_access_token(token) is None

def test_invalid_password_verification():
    hashed = get_password_hash("secret")
    assert not verify_password("invalid", hashed)