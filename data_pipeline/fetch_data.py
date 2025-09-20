import os
import aiohttp
import asyncio
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = "https://apiv3.apifootball.com/"
LEAGUE_ID = "152"  # Premier League
SEASON_START = "2023-08-01"
SEASON_END = "2024-05-31"

async def fetch_events_for_date_range(start_date: str, end_date: str, league_id: str, api_key: str):
    """Fetch match events for a specific date range"""
    events = []
    
    async with aiohttp.ClientSession() as session:
        url = f"{API_BASE_URL}?action=get_events&from={start_date}&to={end_date}&league_id={league_id}&APIkey={api_key}"
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list):
                        events.extend(data)
                    print(f"Fetched {len(data) if isinstance(data, list) else 0} events for {start_date} to {end_date}")
                else:
                    print(f"Error fetching events: HTTP {response.status}")
        except Exception as e:
            print(f"Exception fetching events: {e}")
    
    return events

async def fetch_all_season_data():
    """Fetch all match events for the entire season"""
    api_key = os.getenv('API_FOOTBALL_KEY')
    
    if not api_key:
        print("Error: API_FOOTBALL_KEY not found in environment")
        return
    
    print(f"Fetching data for League ID {LEAGUE_ID} from {SEASON_START} to {SEASON_END}")
    
    # Fetch events in monthly chunks to avoid rate limits
    start_date = datetime.strptime(SEASON_START, "%Y-%m-%d")
    end_date = datetime.strptime(SEASON_END, "%Y-%m-%d")
    
    all_events = []
    current_date = start_date
    
    while current_date <= end_date:
        # Calculate month-end date
        if current_date.month == 12:
            next_month = current_date.replace(year=current_date.year + 1, month=1, day=1)
        else:
            next_month = current_date.replace(month=current_date.month + 1, day=1)
        
        month_end = min(next_month - timedelta(days=1), end_date)
        
        chunk_start = current_date.strftime("%Y-%m-%d")
        chunk_end = month_end.strftime("%Y-%m-%d")
        
        print(f"Fetching events from {chunk_start} to {chunk_end}")
        
        events = await fetch_events_for_date_range(chunk_start, chunk_end, LEAGUE_ID, api_key)
        all_events.extend(events)
        
        # Rate limiting delay
        await asyncio.sleep(1)
        current_date = next_month
    
    print(f"Total events fetched: {len(all_events)}")
    
    # Save to file
    output_file = "data_pipeline/raw_events.json"
    with open(output_file, 'w') as f:
        json.dump(all_events, f, indent=2)
    
    print(f"Events saved to {output_file}")
    
    # Show data structure summary
    if all_events:
        print(f"Sample event has {len(all_events[0])} fields")
        print("Fields:", list(all_events[0].keys())[:5], "...")

if __name__ == "__main__":
    asyncio.run(fetch_all_season_data())