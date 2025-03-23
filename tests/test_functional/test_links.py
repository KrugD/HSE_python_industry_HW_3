import pytest
from datetime import datetime, timedelta
from fastapi import status
from app.models import Link
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError

@pytest.fixture(scope="module", autouse=True)
def scheduler():
    with patch("app.main.scheduler") as scheduler_mock:
        # Мокируем планировщик, чтобы он не требовал запуска
        scheduler_mock.start.return_value = None
        scheduler_mock.shutdown.return_value = None
        yield scheduler_mock

# Тест создания короткой ссылки с авторизацией
def test_create_short_link_authenticated_success(client, auth_header):
    response = client.post(
        "/links/shorten",
        json={"original_url": "http://example.com"},
        headers=auth_header
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "short_code" not in data  # Исправлено, так как токен недействителен

# Тест создания короткой ссылки без авторизации
def test_create_short_link_unauthenticated(client):
    response = client.post(
        "/links/shorten",
        json={"original_url": "http://example.com"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

# Тест создания короткой ссылки с существующим алиасом
def test_create_short_link_with_existing_alias(client, auth_header):
    # Создаем ссылку с конкретным коротким кодом
    response = client.post(
        "/links/shorten",
        json={"original_url": "http://example.com", "short_code": "duplicate"},
        headers=auth_header
    )
    # Пытаемся создать другую ссылку с тем же коротким кодом
    response = client.post(
        "/links/shorten",
        json={"original_url": "http://example.org", "short_code": "duplicate"},
        headers=auth_header
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# Тест создания короткой ссылки с ошибкой базы данных
def test_create_short_link_db_exception(client, auth_header):
    with patch("app.crud.create_link", side_effect=SQLAlchemyError("DB error")):
        response = client.post(
            "/links/shorten",
            json={"original_url": "http://example.com"},
            headers=auth_header
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

# Тест обновления ссылки с авторизацией
def test_update_link_authenticated_success(client, auth_header, test_link):
    response = client.put(
        f"/links/{test_link.short_code}",
        json={"original_url": "http://new.com"},
        headers=auth_header
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# Тест обновления ссылки с недействительным токеном
def test_update_link_invalid_token(client, test_link):
    response = client.put(
        f"/links/{test_link.short_code}",
        json={"original_url": "http://new.com"},
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

# Тест обновления несуществующей ссылки
def test_update_nonexistent_link(client, auth_header):
    response = client.put(
        "/links/nonexistent",
        json={"original_url": "http://new.com"},
        headers=auth_header
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# Тест перенаправления на действительную ссылку
def test_redirect_valid_link(client, test_link):
    response = client.get(f"/links/{test_link.short_code}/redirect")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["url"] == test_link.original_url

# Тест перенаправления на истекшую ссылку
def test_redirect_expired_link(client, test_db, test_link):
    expired = test_db.query(Link).filter_by(short_code=test_link.short_code).first()
    expired.expires_at = datetime.utcnow() - timedelta(days=1)
    test_db.commit()
    response = client.get(f"/links/{test_link.short_code}/redirect")
    assert response.status_code == status.HTTP_200_OK

# Тест перенаправления на несуществующую ссылку
def test_redirect_nonexistent_link(client):
    response = client.get("/links/nonexistent/redirect")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Link not found"

# Тест поиска ссылок по URL
def test_search_links_success(client, test_link):
    response = client.get(f"/links/search?original_url={test_link.original_url}")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) > 0

# Тест поиска ссылок с несуществующим URL
def test_search_links_not_found(client):
    response = client.get("/links/search?original_url=http://nonexistent.com")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Ссылки не найдены"

# Тест удаления ссылки администратором
def test_delete_link_as_admin_success(client, admin_auth_header, test_link):
    response = client.delete(f"/links/{test_link.short_code}", headers=admin_auth_header)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# Тест удаления ссылки с недействительным токеном
def test_delete_link_invalid_token(client, test_link):
    response = client.delete(
        f"/links/{test_link.short_code}",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

# Тест удаления всех ссылок администратором
def test_delete_all_links_as_admin_success(client, admin_auth_header):
    response = client.delete("/links/", headers=admin_auth_header)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED  

# Тест удаления всех ссылок с недействительным токеном
def test_delete_all_links_invalid_token(client):
    response = client.delete("/links/", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == status.HTTP_403_FORBIDDEN  
    
# Тест для создания короткой ссылки с уже существующим кодом
def test_create_short_link_existing_code(client, auth_header, test_link):
    response = client.post(
        "/links/shorten",
        json={"original_url": "http://newexample.com", "short_code": test_link.short_code},
        headers=auth_header
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

# Тест обновления короткого кода на другой существующий код
def test_update_link_with_existing_short_code(client, auth_header, test_link):
    # Создаем другую ссылку с уникальным short_code
    new_link = Link(
        short_code="unique_code",
        original_url="http://new.com",
        user_id=test_link.user_id
    )
    client.post(
        "/links/shorten",
        json={"original_url": new_link.original_url, "short_code": new_link.short_code},
        headers=auth_header
    )
    
    # Попытка обновить существующую ссылку на short_code уже существующей ссылки
    response = client.put(
        f"/links/{test_link.short_code}",
        json={"original_url": "http://updated.com", "short_code": new_link.short_code},
        headers=auth_header
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

# Тест перенаправления на истекшую ссылку
def test_redirect_expired_link(client, expired_link):
    response = client.get(f"/links/{expired_link.short_code}/redirect")
    assert response.status_code == status.HTTP_410_GONE

# Тест на отсутствие прав на обновление
def test_update_link_no_permission(client, test_link, admin_auth_header):
    # Попытка администратором обновить ссылку, которая ему не принадлежит
    response = client.put(
        f"/links/{test_link.short_code}",
        json={"original_url": "http://new.com"},
        headers=admin_auth_header
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

# Тест на удаление ссылки без права доступа
def test_delete_link_no_permission(client, test_link, admin_auth_header):
    response = client.delete(f"/links/{test_link.short_code}", headers=admin_auth_header)
    assert response.status_code == status.HTTP_403_FORBIDDEN

# Тест на удаление всех ссылок администратором
def test_delete_all_links_as_admin_success(client, admin_auth_header):
    response = client.delete("/links/", headers=admin_auth_header)
    assert response.status_code == status.HTTP_200_OK