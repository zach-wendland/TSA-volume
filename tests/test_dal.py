import types
from app import dal
from app.models import VolumeRow
from datetime import date

class FakeTable:
    def __init__(self): self.calls = []
    def upsert(self, batch, on_conflict=None):
        self.calls.append(("upsert", len(batch), on_conflict))
        return self
    def execute(self):
        return types.SimpleNamespace(data=[{"ok": True}])

class FakeClient:
    def table(self, name):
        assert name == "tsa_passenger_volumes"
        return FakeTable()

def fake_client():
    return FakeClient()

def test_upsert_rows_monkeypatch(monkeypatch):
    monkeypatch.setattr(dal, "_client", fake_client)
    rows = [
        VolumeRow(date=date(2025,11,9), current_year_volume=1),
        VolumeRow(date=date(2025,11,8), current_year_volume=2),
    ]
    count = dal.upsert_rows(rows)
    assert count == 2
