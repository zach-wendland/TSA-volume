# TSA Passenger Volume Scraper

A serverless Python API that scrapes TSA passenger volume data and stores it in Supabase. Deployed on Vercel with optional cron scheduling.

## Features

- Serverless FastAPI application deployable on Vercel
- Pure scraper logic with unit tests
- Supabase data access layer with safe server-side service role usage
- Upsert on date to avoid duplicates
- Pytest unit tests that mock network and DB
- Optional daily cron schedule

## Project Structure

```
vercel-supabase-tsa/
  api/
    index.py                 # FastAPI app (Vercel entry)
  app/
    __init__.py
    scraper.py               # pure HTML fetch + parse
    dal.py                   # Supabase upsert logic
    models.py                # pydantic schemas
    settings.py              # env handling
    utils.py                 # small helpers (chunking, date)
  tests/
    test_scraper.py
    test_dal.py
    test_api.py
  requirements.txt
  vercel.json
  README.md
```

## Setup

### 1. Supabase Setup

Run this SQL in the Supabase SQL editor to create the table and RLS policies:

```sql
create table if not exists public.tsa_passenger_volumes (
  id bigserial primary key,
  date date unique not null,
  current_year_volume integer,
  previous_year_volume integer,
  two_years_ago_volume integer,
  scraped_at timestamptz not null default now()
);

alter table public.tsa_passenger_volumes enable row level security;

-- Public read (optional demo). Keep writes server-only via service role.
create policy "read_public" on public.tsa_passenger_volumes
  for select to anon using (true);
```

### 2. Environment Variables

Set these in Vercel Project Settings > Environment Variables:

- `SUPABASE_URL` = `https://YOUR-PROJECT-ref.supabase.co`
- `SUPABASE_SERVICE_ROLE_KEY` = `<service role jwt>`
- `SCRAPE_URL` = `https://www.tsa.gov/travel/passenger-volumes` (optional, defaults to TSA site)

**IMPORTANT:** Never expose the service role key to the browser. All writes happen in the serverless function.

### 3. Deploy to Vercel

1. Push this repository to GitHub
2. Import the project in Vercel
3. Add the environment variables
4. Deploy

Your endpoints will be:
- Health check: `GET /api/healthz`
- Run scraper: `GET /api/run`

### 4. Cron Schedule (Optional)

The `vercel.json` file includes a cron configuration to run the scraper daily at 11:00 UTC:

```json
{
  "crons": [
    { "path": "/api/run", "schedule": "0 11 * * *" }
  ]
}
```

You can modify the schedule or remove it if you prefer manual execution.

## Running Tests

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
pytest
```

## API Endpoints

### GET /api/healthz

Health check endpoint.

Response:
```json
{
  "ok": true
}
```

### GET /api/run

Scrapes TSA data and upserts to Supabase.

Response:
```json
{
  "rows_parsed": 365,
  "rows_upserted": 365,
  "source": "https://www.tsa.gov/travel/passenger-volumes"
}
```

## Development

The scraper preserves the original parsing logic:
- Parses dates with multiple format support
- Parses numbers by removing commas and handling "-", "n/a"
- Extracts from the first HTML table
- Skips header row
- Gets date + 3 numeric columns (current, previous, two_years_ago)
- Upserts on conflict with date

## License

MIT
