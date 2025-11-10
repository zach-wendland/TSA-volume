from app.scraper import parse_volumes

SAMPLE_HTML = """
<table>
  <tr><th>Date</th><th>Current Year</th><th>Previous Year</th><th>Two Years Ago</th></tr>
  <tr><td>11/09/2025</td><td>2,123,456</td><td>1,987,654</td><td>1,543,210</td></tr>
  <tr><td>Nov 08, 2025</td><td>2,000,000</td><td>-</td><td>1,400,000</td></tr>
</table>
"""

def test_parse_volumes_basic():
    rows = parse_volumes(SAMPLE_HTML)
    assert len(rows) == 2
    r0 = rows[0]
    assert str(r0.date) == "2025-11-09"
    assert r0.current_year_volume == 2123456
    assert r0.previous_year_volume == 1987654
    assert r0.two_years_ago_volume == 1543210
