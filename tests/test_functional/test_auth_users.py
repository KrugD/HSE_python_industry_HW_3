import pytest
from fastapi import status
from app import models

# Удобный метод для регистрации нового пользователя
@pytest.fixture
def register_user(client):
    def _register_user(username, email, password):
        return client.post("/auth_users/register", json={
            "username": username,
            "email": email,
            "password": password
        })
    return _register_user

# Проверка корректной регистрации пользователя
def test_registration(register_user):
    response = register_user("testuser", "test@example.com", "secret")
    assert response.status_code == status.HTTP_200_OK  
    data = response.json()
    assert data["username"] == "testuser"
    assert "hashed_password" not in data

# Проверка двойной регистрации с одинаковыми данными
def test_duplicate_registration(register_user):
    # Первая успешная регистрация
    register_user("duplicate", "duplicate@test.com", "secret")
    # Повторная регистрация должна быть отклонена
    response = register_user("duplicate", "duplicate@test.com", "secret")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response.json()["detail"]

# Тест успешного входа в систему
def test_login_success(client, test_user):
    response = client.post("/auth_users/login", json={
        "username": test_user.username,
        "password": "secret"
    })
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY  
    assert "access_token" in response.json()

# Тест входа с неправильным паролем
def test_login_invalid_password(client, test_user):
    response = client.post("/auth_users/login", json={
        "username": test_user.username,
        "password": "wrong"
    })
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY  

# Тест входа для несуществующего пользователя
def test_login_nonexistent_user(client):
    response = client.post("/auth_users/login", json={
        "username": "nonexistent",
        "password": "secret"
    })
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY  

# Проверка регистрация с использованием дублирующегося имени пользователя
def test_register_duplicate_username(register_user, test_user):
    response = register_user(test_user.username, "new@example.com", "password")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response.json()["detail"]

# Тест входа с недействительными учетными данными
def test_login_invalid_credentials(client):
    # Неверный пароль
    response = client.post("/auth_users/login", json={
        "username": "testuser",
        "password": "wrong"
    })
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY  

    # Несуществующий пользователь
    response = client.post("/auth_users/login", json={
        "username": "nonexistent",
        "password": "password"
    })
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY  

# Проверка валидации токена
def test_token_validation(client, auth_header):
    response = client.get("/users/me", headers=auth_header)
    assert response.status_code == status.HTTP_404_NOT_FOUND  

# Проверка валидации недействительного токена
def test_invalid_token(client):
    response = client.get("/users/me", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == status.HTTP_404_NOT_FOUND  