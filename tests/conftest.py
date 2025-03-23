import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from app.main import app
from app.database import Base, get_db
from app import models, utils

# Используем SQLite в памяти для тестирования
TEST_DATABASE_URL = "sqlite:///:memory:"

# Настройка движка и сессии для тестовой базы данных
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Фикстура для создания/удаления тестовой базы данных
@pytest.fixture(scope="function", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield  # Фикстура без возвращаемого значения, просто обертка для создания/удаления таблиц
    Base.metadata.drop_all(bind=engine)

# Фикстура базы данных с транзакционным управлением
@pytest.fixture(scope="function")
def test_db():
    connection = engine.connect()
    trans = connection.begin()
    db = TestingSessionLocal(bind=connection)
    try:
        yield db
    finally:
        db.close()
        trans.rollback()
        connection.close()

# Фикстура планировщика задач - мокируем планировщик
@pytest.fixture(scope="module")
def scheduler():
    with patch("app.main.scheduler") as scheduler_mock:
        yield scheduler_mock

# Фикстура клиента для тестирования API
@pytest.fixture
def client(test_db, scheduler):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

# Фикстура тестового пользователя
@pytest.fixture
def test_user(test_db):
    user = models.User(
        username="testuser",
        email="testuser@example.com",
        hashed_password=utils.get_password_hash("secret"),
        role="user"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

# Фикстура администратора
@pytest.fixture
def admin_user(test_db):
    user = models.User(
        username="admin",
        email="admin@example.com",
        hashed_password=utils.get_password_hash("adminsecret"),
        role="admin"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

# Фикстура для авторизационных заголовков (обычный пользователь)
@pytest.fixture
def auth_header(client, test_user):
    response = client.post(
        "/auth_users/login",
        json={"username": test_user.username, "password": "secret"}
    )
    token = response.json().get("access_token")  # Получаем токен из ответа
    return {"Authorization": f"Bearer {token}"}

# Фикстура для авторизационных заголовков (администратор)
@pytest.fixture
def admin_auth_header(client, admin_user):
    response = client.post(
        "/auth_users/login",
        json={"username": admin_user.username, "password": "adminsecret"}
    )
    token = response.json().get("access_token")  # Получаем токен из ответа
    return {"Authorization": f"Bearer {token}"}

# Фикстура для создания тестовой ссылки
@pytest.fixture
def test_link(test_db, test_user):
    link = models.Link(
        short_code="testcode",
        original_url="http://example.com",
        user_id=test_user.id
    )
    test_db.add(link)
    test_db.commit()
    test_db.refresh(link)
    return link

# Фикстура для создания истекшей ссылки
@pytest.fixture
def expired_link(test_db, test_user):
    link = models.Link(
        short_code="expired",
        original_url="http://expired.com",
        expires_at=datetime.utcnow() - timedelta(days=1),  # Ссылка истекла
        user_id=test_user.id
    )
    test_db.add(link)
    test_db.commit()
    test_db.refresh(link)
    return link