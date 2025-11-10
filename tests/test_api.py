from fastapi.testclient import TestClient
from api.index import app
from app import scraper, dal
from app.models import VolumeRow
from datetime import date

def test_api_run(monkeypatch):
    def fake_scrape():
        return [VolumeRow(date=date(2025,11,9), current_year_volume=123)]
    def fake_upsert(rows):
        assert len(rows) == 1
        return 1

    monkeypatch.setattr(scraper, "scrape", fake_scrape)
    monkeypatch.setattr(dal, "upsert_rows", fake_upsert)

    client = TestClient(app)
    r = client.get("/api/run")
    assert r.status_code == 200
    j = r.json()
    assert j["rows_parsed"] == 1
    assert j["rows_upserted"] == 1
    assert "source" in j
