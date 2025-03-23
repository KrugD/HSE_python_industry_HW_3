import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.crud import create_link, get_link, get_links_by_url, delete_link, delete_expired_links
from app.models import Link
from app.database import Base

@pytest.fixture
def test_db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_create_link(test_db_session):
    link = Link(short_code="test", original_url="http://example.com")
    result = create_link(test_db_session, link)
    assert result.short_code == "test"
    assert result.original_url == "http://example.com"

def test_get_link(test_db_session):
    link = Link(short_code="gettest", original_url="http://gettest.com")
    test_db_session.add(link)
    test_db_session.commit()
    
    result = get_link(test_db_session, "gettest")
    assert result is not None
    assert result.short_code == "gettest"
    assert result.original_url == "http://gettest.com"

def test_get_links_by_url(test_db_session):
    original_url = "http://example.com"
    link = Link(short_code="urltest", original_url=original_url)
    test_db_session.add(link)
    test_db_session.commit()
    
    result = get_links_by_url(test_db_session, original_url)
    assert len(result) == 1
    assert result[0].short_code == "urltest"

def test_delete_link(test_db_session):
    link = Link(short_code="deletetest", original_url="http://delete.com")
    test_db_session.add(link)
    test_db_session.commit()
    
    result = delete_link(test_db_session, "deletetest")
    assert result is True
    
    # Trying to get the deleted link should return None
    assert get_link(test_db_session, "deletetest") is None

def test_delete_expired_links(test_db_session):
    current_time = datetime.utcnow()
    
    link1 = Link(short_code="valid", original_url="http://valid.com", expires_at=current_time + timedelta(days=1))
    link2 = Link(short_code="expired", original_url="http://expired.com", expires_at=current_time - timedelta(days=1))
    
    test_db_session.add(link1)
    test_db_session.add(link2)
    test_db_session.commit()
    
    result = delete_expired_links(test_db_session)
    
    assert result == 1  # Only one expired link
    assert get_link(test_db_session, "expired") is None
    assert get_link(test_db_session, "valid") is not None