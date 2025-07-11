import numpy as np
import os
import pandas as pd

from utils.inference import perform_audio_inference

def predict_bird(audio_path, model_class, model_path, mapping_csv):
    """
    Predict bird species from audio file and display results with confidence.
    
    Args:
        audio_path (str): Path to the audio file to analyze
        model_class (type): Class of the CNN model to use (e.g., OldBirdCNN)
        model_path (str): Path to the .pth model weights file
        mapping_csv (str): Path to CSV file with columns: class_id, scientific_name, common_name
    
    Returns:
        dict: Dictionary containing predicted class_id, common_name, scientific_name, and confidence
        
    Raises:
        FileNotFoundError: If mapping_csv doesn't exist
        ValueError: If mapping CSV doesn't have required columns
    """
    
    # Validate mapping CSV file
    if not os.path.exists(mapping_csv):
        raise FileNotFoundError(f"Mapping CSV file not found: {mapping_csv}")
    
    # Load mapping CSV
    try:
        mapping_df = pd.read_csv(mapping_csv)
        
        required_columns = ['class_id', 'scientific_name', 'common_name']
        if not all(col in mapping_df.columns for col in required_columns):
            raise ValueError(f"Mapping CSV must contain columns: {required_columns}")
        
    except Exception as e:
        raise ValueError(f"Error reading mapping CSV: {e}")
    
    # Get average probabilities from inference
    try:
        average_probabilities = perform_audio_inference(audio_path, model_class, model_path)
        
    except Exception as e:
        raise
    
    # Find the class with highest probability
    predicted_class_id = np.argmax(average_probabilities)
    confidence = average_probabilities[predicted_class_id]
    
    # Get bird information from mapping
    bird_info = mapping_df[mapping_df['class_id'] == predicted_class_id]
    
    if bird_info.empty:
        raise ValueError(f"Class ID {predicted_class_id} not found in mapping CSV")
    
    common_name = bird_info.iloc[0]['common_name']
    scientific_name = bird_info.iloc[0]['scientific_name']
    
    # Return structured results
    return {
        'species': common_name,
        'scientific_name': scientific_name,
        'confidence': float(confidence),
    }
