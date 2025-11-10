from fastapi import FastAPI, Response, status
from fastapi.responses import JSONResponse
from app.scraper import scrape
from app.dal import upsert_rows
from app.models import RunResult
from app.settings import SCRAPE_URL

app = FastAPI()

@app.get("/api/healthz")
def healthz():
    return {"ok": True}

@app.get("/api/run", response_model=RunResult)
def run_scrape():
    rows = scrape()
    upserted = upsert_rows(rows)
    return RunResult(
        rows_parsed=len(rows),
        rows_upserted=upserted,
        source=SCRAPE_URL
    )

# Vercel looks for a default export named "app"
