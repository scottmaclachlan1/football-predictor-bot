# Football Predictor Bot

A Discord bot that provides football match predictions and real match results using slash commands.

## Features

- `/predict` - Get a hard-coded football match prediction
- `/result` - Get the last match result between two specified teams (requires API key)

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your tokens:
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   API_FOOTBALL_KEY=your_api_football_key_here
   ```

3. Get your API-Football key:
   - Visit [API-Football](https://apifootball.com/)
   - Sign up for a free account
   - Get your API key from the dashboard

4. Run the bot:
   ```
   python bot.py
   ```

## Commands

### `/predict`
Returns a hard-coded match prediction.

### `/result team1 team2`
Returns the last match result between two teams.
- `team1`: First team name (e.g., "Manchester United")
- `team2`: Second team name (e.g., "Liverpool")

Example: `/result Manchester United Liverpool`

## API Information

This bot uses the API-Football service to fetch real match data. The free tier includes:
- Limited requests per day
- Access to head-to-head match data
- Historical match results

For more information, visit [API-Football Documentation](https://apifootball.com/documentation-v1).