# Football Predictor Bot

Discord bot with machine learning predictions for football matches.

<img width="634" height="307" alt="image" src="https://github.com/user-attachments/assets/4c4769e7-5dd1-4f19-a447-307b20c67d82" />

## Overview

Built with Python, Discord.py, and scikit-learn. Uses real football data from API-Football to train a RandomForest model that predicts match outcomes.

## Tech Stack

- **Backend**: Python 3.13
- **ML**: scikit-learn (RandomForestClassifier)
- **Bot**: discord.py with slash commands
- **Data**: API-Football API
- **Storage**: JSON/CSV files

## Features

- `/predict home_team away_team` - ML-powered match prediction with probabilities
- `/result team1 team2` - Historical match results
- Trained model with 71% accuracy on Premier League data

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Create `.env` file**:
   ```
   DISCORD_TOKEN=your_discord_bot_token
   API_FOOTBALL_KEY=your_api_football_key
   ```

3. **Train the model**:
   ```bash
   python setup_ml_pipeline.py
   ```

4. **Run the bot**:
   ```bash
   python bot.py
   ```

## ML Pipeline

The bot includes a complete machine learning pipeline:

1. **Data Collection** (`fetch_data.py`) - Pulls historical match events
2. **Feature Engineering** (`build_features.py`) - Extracts team form, standings, H2H records
3. **Model Training** (`train_model.py`) - Trains RandomForest on 6 features
4. **Real-time Prediction** - Uses cached model for instant predictions

## Commands

- `/predict Arsenal Chelsea` - Returns prediction with win/draw/loss probabilities
- `/result Manchester United Liverpool` - Shows last match between teams
- `/sync` - Manual command sync (admin only)

## Architecture

```
bot.py (main)
├── ML model loading & caching
├── API data fetching
├── Feature vector generation
└── Discord slash command handlers

data_pipeline/
├── fetch_data.py - Historical data collection
├── build_features.py - Feature engineering
└── train_model.py - Model training & evaluation
```

## API Usage

Uses API-Football free tier:
- Match events and standings
- Head-to-head data
- Rate limited to prevent 429 errors

## Requirements

See `requirements.txt` for full dependency list. Key packages:
- discord.py
- scikit-learn
- pandas
- aiohttp
