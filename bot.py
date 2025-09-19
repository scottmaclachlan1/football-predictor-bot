import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import aiohttp
from typing import Optional

bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())
API_FOOTBALL_BASE_URL = "https://apiv3.apifootball.com/"

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

async def fetch_team_head_to_head(team1: str, team2: str, api_key: str) -> Optional[dict]:
    """Fetch head-to-head data between two teams"""
    try:
        async with aiohttp.ClientSession() as session:
            api_key = api_key.strip()
            
            import urllib.parse
            encoded_team1 = urllib.parse.quote(team1)
            encoded_team2 = urllib.parse.quote(team2)
            
            url = f"{API_FOOTBALL_BASE_URL}?action=get_H2H&firstTeam={encoded_team1}&secondTeam={encoded_team2}&APIkey={api_key}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    try:
                        return await response.json()
                    except:
                        return None
                else:
                    return None
    except:
        return None

def format_match_result(match_data: dict) -> str:
    """Format match data"""
    try:
        match_date = match_data.get('match_date', 'Unknown date')
        home_team = match_data.get('match_hometeam_name', 'Unknown team')
        away_team = match_data.get('match_awayteam_name', 'Unknown team')
        home_score = match_data.get('match_hometeam_score', '?')
        away_score = match_data.get('match_awayteam_score', '?')
        league = match_data.get('league_name', 'Unknown league')
        
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

@bot.tree.command(name="predict", description="Get a football match prediction")
async def predict(interaction: discord.Interaction):
    """Get match prediction"""
    prediction = "Manchester United vs Liverpool: Liverpool wins 3-1."
    await interaction.response.send_message(prediction)

@bot.tree.command(name="sync", description="Sync slash commands (admin only)")
async def sync(interaction: discord.Interaction):
    """Sync slash commands"""
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You need administrator permissions.", ephemeral=True)
        return
    
    try:
        synced = await bot.tree.sync()
        await interaction.response.send_message(f"✅ Synced {len(synced)} command(s)", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to sync commands: {e}", ephemeral=True)

@bot.tree.command(name="result", description="Get the last match result between two teams")
async def result(interaction: discord.Interaction, team1: str, team2: str):
    """Get match result between two teams"""
    api_key = os.getenv('API_FOOTBALL_KEY')
    
    if not api_key:
        await interaction.response.send_message("❌ API key not configured.")
        return
    
    await interaction.response.defer()
    
    try:
        h2h_data = await fetch_team_head_to_head(team1, team2, api_key)
        
        if not h2h_data or not isinstance(h2h_data, dict):
            await interaction.followup.send("❌ Could not fetch match data.")
            return
        
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

if __name__ == "__main__":
    load_dotenv()
    
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Error: DISCORD_TOKEN not found in .env file")
        exit(1)
    
    print("Bot starting...")
    bot.run(token)