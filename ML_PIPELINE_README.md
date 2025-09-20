# ML Pipeline

Machine learning pipeline for football match prediction using scikit-learn.

## Quick Start

```bash
python setup_ml_pipeline.py  # Runs entire pipeline
python bot.py                # Start bot with ML predictions
```

## Pipeline Components

1. **Data Collection** - Fetches historical match events from API-Football
2. **Feature Engineering** - Extracts team form, standings, H2H records  
3. **Model Training** - RandomForestClassifier with 71.1% accuracy
4. **Real-time Prediction** - Bot uses trained model for live predictions

## ML Features

- `form_home/away` - Wins in last 5 matches
- `standing_home/away` - Current league position
- `h2h_home_wins/h2h_away_wins` - Historical head-to-head record

## Model Performance

- **Algorithm**: RandomForestClassifier (100 trees, max_depth=10)
- **Accuracy**: 71.1% on test set
- **Classes**: Home Win, Draw, Away Win
- **Training Data**: 380+ Premier League matches

## Usage

```python
# Bot automatically loads model on startup
model = joblib.load('models/predictor.joblib')
probabilities = model.predict_proba(feature_vector)
```

## Configuration

Edit league settings in `fetch_data.py`:
```python
LEAGUE_ID = "152"        # Premier League
SEASON_START = "2023-08-01"
SEASON_END = "2024-05-31"
```

## API Limits

- Free tier: 100 requests/day
- Pipeline includes rate limiting delays
- Data files included to avoid API calls on first run