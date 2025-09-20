import json
import pandas as pd
import aiohttp
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = "https://apiv3.apifootball.com/"
LEAGUE_ID = "152"  # Premier League

async def fetch_standings(api_key: str, league_id: str):
    """Fetch current league standings"""
    async with aiohttp.ClientSession() as session:
        url = f"{API_BASE_URL}?action=get_standings&league_id={league_id}&APIkey={api_key}"
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data if isinstance(data, list) else []
        except:
            pass
    return []

async def fetch_team_recent_matches(api_key: str, team_id: str, limit: int = 5):
    """Fetch recent matches for a team"""
    async with aiohttp.ClientSession() as session:
        url = f"{API_BASE_URL}?action=get_events&team_id={team_id}&limit={limit}&APIkey={api_key}"
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data if isinstance(data, list) else []
        except:
            pass
    return []

def calculate_form(matches: list, team_id: str):
    """Calculate wins/draws/losses from recent matches"""
    wins = draws = losses = 0
    
    for match in matches:
        if match.get('match_hometeam_id') == team_id:
            # Team is home
            home_score = match.get('match_hometeam_score', '0')
            away_score = match.get('match_awayteam_score', '0')
            
            if home_score.isdigit() and away_score.isdigit():
                if int(home_score) > int(away_score):
                    wins += 1
                elif int(home_score) == int(away_score):
                    draws += 1
                else:
                    losses += 1
        
        elif match.get('match_awayteam_id') == team_id:
            # Team is away
            home_score = match.get('match_hometeam_score', '0')
            away_score = match.get('match_awayteam_score', '0')
            
            if home_score.isdigit() and away_score.isdigit():
                if int(away_score) > int(home_score):
                    wins += 1
                elif int(away_score) == int(home_score):
                    draws += 1
                else:
                    losses += 1
    
    return wins, draws, losses

def calculate_h2h_record(events: list, home_team_id: str, away_team_id: str):
    """Calculate head-to-head record between two teams"""
    home_wins = away_wins = draws = 0
    
    for match in events:
        if (match.get('match_hometeam_id') == home_team_id and 
            match.get('match_awayteam_id') == away_team_id) or \
           (match.get('match_hometeam_id') == away_team_id and 
            match.get('match_awayteam_id') == home_team_id):
            
            home_score = match.get('match_hometeam_score', '0')
            away_score = match.get('match_awayteam_score', '0')
            
            if home_score.isdigit() and away_score.isdigit():
                if int(home_score) > int(away_score):
                    if match.get('match_hometeam_id') == home_team_id:
                        home_wins += 1
                    else:
                        away_wins += 1
                elif int(home_score) < int(away_score):
                    if match.get('match_hometeam_id') == home_team_id:
                        away_wins += 1
                    else:
                        home_wins += 1
                else:
                    draws += 1
    
    return home_wins, away_wins, draws

async def extract_features(events: list, api_key: str):
    """Extract ML features from events data"""
    features = []
    
    # Create standings lookup
    standings_data = await fetch_standings(api_key, LEAGUE_ID)
    standings_lookup = {}
    
    if standings_data:
        for team in standings_data:
            team_id = team.get('team_id', '')
            position = team.get('overall_league_position', 20)
            standings_lookup[team_id] = int(position) if str(position).isdigit() else 20
    
    print(f"Loaded standings for {len(standings_lookup)} teams")
    
    # Get unique fixtures (avoid duplicates)
    fixtures_processed = set()
    
    for event in events:
        match_id = event.get('match_id', '')
        home_team_id = event.get('match_hometeam_id', '')
        away_team_id = event.get('match_awayteam_id', '')
        home_score = event.get('match_hometeam_score', '?')
        away_score = event.get('match_awayteam_score', '?')
        
        # Skip if already processed or missing data
        if (match_id in fixtures_processed or 
            not home_team_id or not away_team_id or 
            home_score == '?' or away_score == '?'):
            continue
        
        # Skip if scores are not numeric
        if not (home_score.isdigit() and away_score.isdigit()):
            continue
        
        fixtures_processed.add(match_id)
        
        # Get recent form for both teams
        home_matches = await fetch_team_recent_matches(api_key, home_team_id, 10)
        away_matches = await fetch_team_recent_matches(api_key, away_team_id, 10)
        
        home_wins, home_draws, home_losses = calculate_form(home_matches, home_team_id)
        away_wins, away_draws, away_losses = calculate_form(away_matches, away_team_id)
        
        # Calculate H2H record
        h2h_home_wins, h2h_away_wins, h2h_draws = calculate_h2h_record(events, home_team_id, away_team_id)
        
        # Get standings
        home_standing = standings_lookup.get(home_team_id, 20)
        away_standing = standings_lookup.get(away_team_id, 20)
        
        # Determine result (1 = home win, 0 = draw, -1 = away win)
        if int(home_score) > int(away_score):
            result = 1  # Home win
        elif int(home_score) < int(away_score):
            result = -1  # Away win
        else:
            result = 0  # Draw
        
        # Create feature vector
        feature_vector = {
            'home_id': home_team_id,
            'away_id': away_team_id,
            'form_home': home_wins,  # Just wins for simplicity
            'form_away': away_wins,
            'standing_home': home_standing,
            'standing_away': away_standing,
            'h2h_home_wins': h2h_home_wins,
            'h2h_away_wins': h2h_away_wins,
            'result': result
        }
        
        features.append(feature_vector)
        
        # Rate limiting
        await asyncio.sleep(0.5)
    
    return features

async def build_features():
    """Main function to build features from raw events"""
    api_key = os.getenv('API_FOOTBALL_KEY')
    
    if not api_key:
        print("Error: API_FOOTBALL_KEY not found in environment")
        return
    
    # Load raw events
    try:
        with open('data_pipeline/raw_events.json', 'r') as f:
            events = json.load(f)
        print(f"Loaded {len(events)} events")
    except FileNotFoundError:
        print("Error: raw_events.json not found. Run fetch_data.py first.")
        return
    
    # Extract features
    print("Extracting features...")
    features = await extract_features(events, api_key)
    
    # Create DataFrame and save
    df = pd.DataFrame(features)
    output_file = 'data_pipeline/features.csv'
    df.to_csv(output_file, index=False)
    
    print(f"Features saved to {output_file}")
    print(f"Dataset shape: {df.shape}")
    print(f"Features: {list(df.columns)}")
    print(f"Result distribution:")
    print(df['result'].value_counts())

if __name__ == "__main__":
    asyncio.run(build_features())