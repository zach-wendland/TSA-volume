import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SCRAPE_URL = os.getenv("SCRAPE_URL", "https://www.tsa.gov/travel/passenger-volumes")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    # Don't crash import for tests; API will 500 if truly missing at runtime
    pass
