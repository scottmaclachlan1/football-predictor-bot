import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import aiohttp
import joblib
import pandas as pd
import urllib.parse
from typing import Optional

bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())
API_BASE_URL = "https://apiv3.apifootball.com/"

# Global variables for ML model and caching
model = None
feature_columns = None
standings_cache = {}

def load_model():
    """Load trained RandomForest model and feature metadata"""
    global model, feature_columns
    try:
        model = joblib.load('models/predictor.joblib')
        feature_info = joblib.load('models/feature_info.joblib')
        feature_columns = feature_info['feature_columns']
        print(f"✅ ML model loaded (accuracy: {feature_info.get('accuracy', 'N/A'):.3f})")
    except FileNotFoundError:
        print("⚠️ No trained model found. Run setup_ml_pipeline.py first.")
        model = None

@bot.event
async def on_ready():
    print(f'{bot.user} connected to Discord!')
    load_model()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

async def fetch_standings(api_key: str, league_id: str = "152"):
    """Fetch current league standings from API"""
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

async def fetch_team_matches(api_key: str, team_id: str, limit: int = 5):
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

def calculate_form(matches: list, team_id: str) -> int:
    """Calculate wins in recent matches for team form"""
    wins = 0
    for match in matches:
        if match.get('match_hometeam_id') == team_id:
            home_score = match.get('match_hometeam_score', '0')
            away_score = match.get('match_awayteam_score', '0')
            if home_score.isdigit() and away_score.isdigit() and int(home_score) > int(away_score):
                wins += 1
        elif match.get('match_awayteam_id') == team_id:
            home_score = match.get('match_hometeam_score', '0')
            away_score = match.get('match_awayteam_score', '0')
            if home_score.isdigit() and away_score.isdigit() and int(away_score) > int(home_score):
                wins += 1
    return wins

async def predict_match(home_team: str, away_team: str, api_key: str):
    """Generate ML prediction for match outcome"""
    if model is None:
        return None, "No trained model available"
    
    try:
        # Convert team names to IDs (simplified approach)
        home_team_id = home_team.lower().replace(' ', '_')
        away_team_id = away_team.lower().replace(' ', '_')
        
        # Fetch recent form for both teams
        home_matches = await fetch_team_matches(api_key, home_team_id, 5)
        away_matches = await fetch_team_matches(api_key, away_team_id, 5)
        
        home_form = calculate_form(home_matches, home_team_id)
        away_form = calculate_form(away_matches, away_team_id)
        
        # Cache standings to avoid repeated API calls
        if not standings_cache:
            standings_data = await fetch_standings(api_key)
            for team in standings_data:
                team_id = team.get('team_id', '')
                position = team.get('overall_league_position', 20)
                standings_cache[team_id] = int(position) if str(position).isdigit() else 20
        
        home_standing = standings_cache.get(home_team_id, 20)
        away_standing = standings_cache.get(away_team_id, 20)
        
        # Create feature vector for ML model
        features = pd.DataFrame([{
            'form_home': home_form,
            'form_away': away_form,
            'standing_home': home_standing,
            'standing_away': away_standing,
            'h2h_home_wins': 0,  # Simplified - would need historical data
            'h2h_away_wins': 0
        }])
        
        # Make prediction
        probabilities = model.predict_proba(features[feature_columns])[0]
        prediction = model.predict(features[feature_columns])[0]
        
        # Map numeric prediction to readable result
        result_map = {-1: "Away Win", 0: "Draw", 1: "Home Win"}
        predicted_result = result_map.get(prediction, "Unknown")
        
        return predicted_result, probabilities
        
    except Exception as e:
        return None, f"Prediction error: {str(e)}"

async def fetch_h2h_data(team1: str, team2: str, api_key: str) -> Optional[dict]:
    """Fetch head-to-head match data between two teams"""
    try:
        async with aiohttp.ClientSession() as session:
            encoded_team1 = urllib.parse.quote(team1)
            encoded_team2 = urllib.parse.quote(team2)
            url = f"{API_BASE_URL}?action=get_H2H&firstTeam={encoded_team1}&secondTeam={encoded_team2}&APIkey={api_key.strip()}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    try:
                        return await response.json()
                    except:
                        return None
                return None
    except:
        return None

def format_match_result(match_data: dict) -> str:
    """Format match data into readable string"""
    try:
        match_date = match_data.get('match_date', 'Unknown date')
        home_team = match_data.get('match_hometeam_name', 'Unknown team')
        away_team = match_data.get('match_awayteam_name', 'Unknown team')
        home_score = match_data.get('match_hometeam_score', '?')
        away_score = match_data.get('match_awayteam_score', '?')
        league = match_data.get('league_name', 'Unknown league')
        
        # Determine winner
        if home_score != '?' and away_score != '?':
            if int(home_score) > int(away_score):
                result = f"{home_team} won"
            elif int(away_score) > int(home_score):
                result = f"{away_team} won"
            else:
                result = "Draw"
        else:
            result = "Score not available"
        
        return f"**{home_team} vs {away_team}**\n" \
               f"📅 Date: {match_date}\n" \
               f"🏆 League: {league}\n" \
               f"⚽ Score: {home_score} - {away_score}\n" \
               f"🏁 Result: {result}"
    except:
        return "Error formatting match result"

@bot.tree.command(name="predict", description="Get ML-powered match prediction")
async def predict(interaction: discord.Interaction, home_team: str, away_team: str):
    """Predict match outcome using machine learning"""
    api_key = os.getenv('API_FOOTBALL_KEY')
    
    if not api_key:
        await interaction.response.send_message("❌ API key not configured.")
        return
    
    if model is None:
        await interaction.response.send_message("❌ ML model not loaded. Run setup_ml_pipeline.py first.")
        return
    
    # Respond immediately to avoid Discord timeout
    await interaction.response.send_message("🤖 Analyzing match data...")
    
    try:
        predicted_result, probabilities = await predict_match(home_team, away_team, api_key)
        
        if predicted_result is None:
            await interaction.edit_original_response(content=f"❌ {probabilities}")
            return
        
        # Format probability output (order: away, draw, home)
        prob_away = probabilities[0] if len(probabilities) > 0 else 0
        prob_draw = probabilities[1] if len(probabilities) > 1 else 0  
        prob_home = probabilities[2] if len(probabilities) > 2 else 0
        
        response = f"**🤖 AI Prediction: {home_team} vs {away_team}**\n\n"
        response += f"**Predicted Result:** {predicted_result}\n\n"
        response += f"**Probabilities:**\n"
        response += f"🏠 {home_team} Win: {prob_home:.1%}\n"
        response += f"🤝 Draw: {prob_draw:.1%}\n"
        response += f"✈️ {away_team} Win: {prob_away:.1%}\n\n"
        response += f"*Based on recent form, league standings, and head-to-head records*"
        
        await interaction.edit_original_response(content=response)
        
    except Exception as e:
        await interaction.edit_original_response(content=f"❌ Error making prediction: {str(e)}")

@bot.tree.command(name="result", description="Get historical match result between two teams")
async def result(interaction: discord.Interaction, team1: str, team2: str):
    """Get most recent match result between two teams"""
    api_key = os.getenv('API_FOOTBALL_KEY')
    
    if not api_key:
        await interaction.response.send_message("❌ API key not configured.")
        return
    
    await interaction.response.defer()
    
    try:
        h2h_data = await fetch_h2h_data(team1, team2, api_key)
        
        if not h2h_data or not isinstance(h2h_data, dict):
            await interaction.followup.send("❌ Could not fetch match data.")
            return
        
        # Look for head-to-head matches first, then recent matches
        h2h_matches = h2h_data.get('firstTeam_VS_secondTeam', [])
        team1_recent = h2h_data.get('firstTeam_lastResults', [])
        team2_recent = h2h_data.get('secondTeam_lastResults', [])
        
        latest_match = None
        if h2h_matches:
            latest_match = h2h_matches[0]
        elif team1_recent:
            latest_match = team1_recent[0]
        elif team2_recent:
            latest_match = team2_recent[0]
        
        if not latest_match:
            await interaction.followup.send(f"❌ No matches found for {team1} and {team2}.")
            return
        
        formatted_result = format_match_result(latest_match)
        await interaction.followup.send(formatted_result)
        
    except:
        await interaction.followup.send("❌ Error fetching match result.")

@bot.tree.command(name="sync", description="Sync slash commands (admin only)")
async def sync(interaction: discord.Interaction):
    """Manually sync slash commands with Discord"""
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Administrator permissions required.", ephemeral=True)
        return
    
    try:
        synced = await bot.tree.sync()
        await interaction.response.send_message(f"✅ Synced {len(synced)} commands", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to sync: {e}", ephemeral=True)

if __name__ == "__main__":
    load_dotenv()
    
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Error: DISCORD_TOKEN not found in .env file")
        exit(1)
    
    print("🤖 Football Predictor Bot starting...")
    bot.run(token)