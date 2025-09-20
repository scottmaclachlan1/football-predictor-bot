import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

def train_model():
    """Train RandomForest classifier on match features"""
    
    # Load features
    try:
        df = pd.read_csv('data_pipeline/features.csv')
        print(f"Loaded dataset with {len(df)} samples")
    except FileNotFoundError:
        print("Error: features.csv not found. Run build_features.py first.")
        return
    
    # Prepare features and target
    feature_columns = ['form_home', 'form_away', 'standing_home', 'standing_away', 
                      'h2h_home_wins', 'h2h_away_wins']
    
    X = df[feature_columns]
    y = df['result']
    
    print(f"Feature matrix shape: {X.shape}")
    print(f"Target distribution: {y.value_counts()}")
    
    # Split data into train/test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"Training set: {X_train.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")
    
    # Train RandomForest classifier
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight='balanced'  # Handle class imbalance
    )
    
    print("Training RandomForest classifier...")
    model.fit(X_train, y_train)
    
    # Evaluate model
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\nModel Performance:")
    print(f"Accuracy: {accuracy:.3f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, 
                              target_names=['Away Win', 'Draw', 'Home Win']))
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nFeature Importance:")
    print(feature_importance)
    
    # Save model and metadata
    model_path = 'models/predictor.joblib'
    joblib.dump(model, model_path)
    print(f"\nModel saved to {model_path}")
    
    # Save feature info for later use
    feature_info = {
        'feature_columns': feature_columns,
        'model_type': 'RandomForestClassifier',
        'accuracy': accuracy,
        'n_estimators': 100,
        'max_depth': 10
    }
    
    joblib.dump(feature_info, 'models/feature_info.joblib')
    print("Feature info saved to models/feature_info.joblib")
    
    return model, feature_columns

if __name__ == "__main__":
    train_model()