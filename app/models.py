from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

class VolumeRow(BaseModel):
    date: date
    current_year_volume: Optional[int] = Field(default=None)
    previous_year_volume: Optional[int] = Field(default=None)
    two_years_ago_volume: Optional[int] = Field(default=None)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

class RunResult(BaseModel):
    rows_parsed: int
    rows_upserted: int
    source: str
