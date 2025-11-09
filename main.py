import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re


class TSAScraper:
    def __init__(self, db_path="tsa_data.db"):
        """Initialize the scraper with database connection"""
        self.db_path = db_path
        self.url = "https://www.tsa.gov/travel/passenger-volumes"
        self.conn = None
        self.cursor = None
        
    def connect_db(self):
        """Connect to SQLite database and create table if it doesn't exist"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Create table with proper schema
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS passenger_volumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                current_year_volume INTEGER,
                previous_year_volume INTEGER,
                two_years_ago_volume INTEGER,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
        print(f"✓ Connected to database: {self.db_path}")
        
    def fetch_page(self):
        """Fetch the TSA passenger volumes page"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(self.url, headers=headers, timeout=10)
            response.raise_for_status()
            print(f"✓ Successfully fetched page from {self.url}")
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching page: {e}")
            return None
            
    def parse_data(self, html_content):
        """Parse the HTML content and extract passenger volume data"""
        if not html_content:
            return []
            
        soup = BeautifulSoup(html_content, 'html.parser')
        data = []
        
        # Find the table containing passenger data
        # TSA typically uses tables or specific div structures for this data
        table = soup.find('table')
        
        if not table:
            print("✗ Could not find data table on page")
            return []
            
        # Parse table rows
        rows = table.find_all('tr')
        print(f"✓ Found {len(rows)} rows in table")
        
        for row in rows[1:]:  # Skip header row
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                try:
                    # Extract date and volume data
                    date_text = cells[0].get_text(strip=True)
                    
                    # Parse date - handle various formats
                    date_obj = self.parse_date(date_text)
                    if not date_obj:
                        continue
                    
                    # Extract passenger volumes (remove commas and convert to int)
                    volumes = []
                    for i in range(1, len(cells)):
                        volume_text = cells[i].get_text(strip=True)
                        volume = self.parse_number(volume_text)
                        volumes.append(volume)
                    
                    # Pad with None if we don't have all columns
                    while len(volumes) < 3:
                        volumes.append(None)
                    
                    data.append({
                        'date': date_obj,
                        'current': volumes[0],
                        'previous': volumes[1] if len(volumes) > 1 else None,
                        'two_years': volumes[2] if len(volumes) > 2 else None
                    })
                    
                except Exception as e:
                    print(f"⚠ Error parsing row: {e}")
                    continue
                    
        print(f"✓ Parsed {len(data)} data records")
        return data
        
    def parse_date(self, date_text):
        """Parse date string into standardized format"""
        # Remove extra whitespace
        date_text = re.sub(r'\s+', ' ', date_text.strip())
        
        # Common date formats TSA might use
        formats = [
            '%m/%d/%Y',      # 11/09/2025
            '%m-%d-%Y',      # 11-09-2025
            '%B %d, %Y',     # November 09, 2025
            '%b %d, %Y',     # Nov 09, 2025
            '%Y-%m-%d',      # 2025-11-09
        ]
        
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_text, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
                
        return None
        
    def parse_number(self, text):
        """Parse number string, removing commas and handling empty values"""
        if not text or text == '-' or text.lower() == 'n/a':
            return None
        # Remove commas and any other non-digit characters except minus
        number_str = re.sub(r'[^\d-]', '', text)
        try:
            return int(number_str) if number_str else None
        except ValueError:
            return None
            
    def save_to_db(self, data):
        """Save parsed data to database"""
        if not data:
            print("⚠ No data to save")
            return 0
            
        inserted = 0
        updated = 0
        
        for record in data:
            try:
                # Try to insert, if date exists, update instead
                self.cursor.execute("""
                    INSERT INTO passenger_volumes 
                    (date, current_year_volume, previous_year_volume, two_years_ago_volume)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(date) DO UPDATE SET
                        current_year_volume = excluded.current_year_volume,
                        previous_year_volume = excluded.previous_year_volume,
                        two_years_ago_volume = excluded.two_years_ago_volume,
                        scraped_at = CURRENT_TIMESTAMP
                """, (record['date'], record['current'], record['previous'], record['two_years']))
                
                if self.cursor.rowcount > 0:
                    inserted += 1
                else:
                    updated += 1
                    
            except sqlite3.IntegrityError as e:
                print(f"⚠ Error saving record for {record['date']}: {e}")
                continue
                
        self.conn.commit()
        print(f"✓ Saved to database: {inserted} new records, {updated} updated")
        return inserted
        
    def display_summary(self):
        """Display summary of data in database"""
        self.cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                MIN(date) as earliest_date,
                MAX(date) as latest_date,
                AVG(current_year_volume) as avg_volume
            FROM passenger_volumes
        """)
        
        result = self.cursor.fetchone()
        print("\n" + "="*60)
        print("DATABASE SUMMARY")
        print("="*60)
        print(f"Total records: {result[0]}")
        print(f"Date range: {result[1]} to {result[2]}")
        if result[3]:
            print(f"Average daily volume: {result[3]:,.0f} passengers")
        print("="*60)
        
        # Show latest 5 records
        print("\nLATEST 5 RECORDS:")
        print("-"*60)
        self.cursor.execute("""
            SELECT date, current_year_volume, previous_year_volume 
            FROM passenger_volumes 
            ORDER BY date DESC 
            LIMIT 5
        """)
        
        for row in self.cursor.fetchall():
            date, current, previous = row
            current_str = f"{current:,}" if current else "N/A"
            previous_str = f"{previous:,}" if previous else "N/A"
            print(f"{date}: {current_str:>15} (prev year: {previous_str:>15})")
        print("-"*60 + "\n")
        
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("✓ Database connection closed")
            
    def run(self):
        """Main execution method"""
        print("\n" + "="*60)
        print("TSA PASSENGER VOLUME SCRAPER")
        print("="*60 + "\n")
        
        try:
            # Connect to database
            self.connect_db()
            
            # Fetch the page
            html_content = self.fetch_page()
            
            if html_content:
                # Parse the data
                data = self.parse_data(html_content)
                
                # Save to database
                if data:
                    self.save_to_db(data)
                    self.display_summary()
                else:
                    print("⚠ No data was parsed from the page")
            else:
                print("✗ Failed to fetch page content")
                
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.close()


if __name__ == "__main__":
    scraper = TSAScraper()
    scraper.run()
