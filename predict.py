# ==========================================
# Verdant AI Plant Disease Detection
# predict.py - Load AI Model + Image Prediction
# ==========================================

import os
import numpy as np  # pyrefly: ignore [missing-import]
import tensorflow as tf  # pyrefly: ignore [missing-import]
from tensorflow.keras.preprocessing import image  # pyrefly: ignore [missing-import]

# -----------------------------
# Load Trained Model
# -----------------------------
MODEL_PATH = "model/plant_disease_model.keras"

model = tf.keras.models.load_model(MODEL_PATH)

# -----------------------------
# Class Names (auto-loaded from dataset)
# -----------------------------
DATASET_PATH = "dataset/PlantVillage-Dataset-master/PlantVillage-Dataset-master/raw/color"

class_names = sorted([
    folder
    for folder in os.listdir(DATASET_PATH)
    if os.path.isdir(os.path.join(DATASET_PATH, folder))
])

print("\n==============================")
print("Classes Loaded Successfully")
print("==============================")
print(class_names)
print(f"Total Classes: {len(class_names)}")

# -----------------------------
# Core Prediction Function
# -----------------------------
def predict_disease(image_path):
    img = image.load_img(image_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0

    prediction = model.predict(img_array)

    predicted_index = np.argmax(prediction)
    confidence = float(np.max(prediction) * 100)

    return predicted_index, confidence


# -----------------------------
# Predict Disease Name
# -----------------------------
def predict(image_path):
    predicted_index, confidence = predict_disease(image_path)
    disease_name = class_names[predicted_index]

    return {
        "disease": disease_name,
        "confidence": round(confidence, 2)
    }


# -----------------------------
# Test Prediction
# -----------------------------
if __name__ == "__main__":
    print("Prediction Started...")

    test_image = "uploads/test.jpg"

    if os.path.exists(test_image):
        result = predict(test_image)

        print("\n==========================")
        print("Prediction Result")
        print("==========================")
        print(f"Disease: {result['disease']}")
        print(f"Confidence: {result['confidence']:.2f}%")
        print("==========================")
    else:
        print("\nNo test image found!")
        print("Copy any leaf image into uploads/")
        print("Rename it to test.jpg")
        print("Model Loaded Successfully")
