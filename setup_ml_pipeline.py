#!/usr/bin/env python3
"""
Setup script to run the entire ML pipeline
Run this once to train your model before using the bot
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout[:200]}...")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("🚀 Setting up Football Predictor ML Pipeline")
    print("=" * 50)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found. Please create it with your API keys.")
        return False
    
    # Step 1: Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        return False
    
    # Step 2: Fetch data
    if not run_command("python data_pipeline/fetch_data.py", "Fetching historical match data"):
        return False
    
    # Step 3: Build features
    if not run_command("python data_pipeline/build_features.py", "Building ML features"):
        return False
    
    # Step 4: Train model
    if not run_command("python data_pipeline/train_model.py", "Training ML model"):
        return False
    
    print("\n🎉 ML Pipeline setup complete!")
    print("✅ You can now run your bot with: python bot.py")
    print("✅ Use /predict <home_team> <away_team> for ML predictions")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
