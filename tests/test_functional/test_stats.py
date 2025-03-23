import pytest
from fastapi import status

def test_get_link_stats(client, test_link):
    response = client.get(f"/stats/{test_link.short_code}/stats")
    assert response.status_code == status.HTTP_200_OK
    stats = response.json()
    assert stats["hits"] == 0
    assert stats["created_at"] is not None

def test_stats_after_redirect(client, test_link):
    # First redirect
    client.get(f"/links/{test_link.short_code}/redirect")
    
    # Check stats
    response = client.get(f"/stats/{test_link.short_code}/stats")
    assert response.json()["hits"] == 1

def test_stats_nonexistent_link(client):
    response = client.get("/stats/invalid/stats")
    assert response.status_code == status.HTTP_404_NOT_FOUND
