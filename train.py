# ==========================================
# Verdant AI Plant Disease Detection
# train.py - Part 1
# TensorFlow Imports + Dataset Loading
# ==========================================

import os
import tensorflow as tf  # pyrefly: ignore [missing-import]
from tensorflow.keras.preprocessing import image_dataset_from_directory  # pyrefly: ignore [missing-import]

from tensorflow.keras.callbacks import ModelCheckpoint
# -----------------------------
# Dataset Path
# -----------------------------
DATASET_PATH = "dataset/PlantVillage-Dataset-master/PlantVillage-Dataset-master/raw/color"

# -----------------------------
# Settings
# -----------------------------
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
SEED = 123

# -----------------------------
# Load Training Dataset
# -----------------------------
train_dataset = image_dataset_from_directory(
    DATASET_PATH,
    validation_split=0.2,
    subset="training",
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

# -----------------------------
# Load Validation Dataset
# -----------------------------
validation_dataset = image_dataset_from_directory(
    DATASET_PATH,
    validation_split=0.2,
    subset="validation",
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

# -----------------------------
# Class Names
# -----------------------------
class_names = train_dataset.class_names

print("\n==============================")
print("Plant Disease Classes Loaded")
print("==============================")
print(class_names)
print(f"\nTotal Classes: {len(class_names)}")

# -----------------------------
# Improve Performance
# -----------------------------
AUTOTUNE = tf.data.AUTOTUNE

train_dataset = train_dataset.prefetch(buffer_size=AUTOTUNE)
validation_dataset = validation_dataset.prefetch(buffer_size=AUTOTUNE)

print("\nDataset Loaded Successfully!")

# ==========================================
# train.py - Part 2
# CNN Model + Training + Save Model
# ==========================================

from tensorflow.keras import layers, models

# -----------------------------
# Data Normalization
# -----------------------------
normalization_layer = layers.Rescaling(1./255)

train_dataset = train_dataset.map(
    lambda x, y: (normalization_layer(x), y)
)

validation_dataset = validation_dataset.map(
    lambda x, y: (normalization_layer(x), y)
)

# -----------------------------
# CNN Model
# -----------------------------
model = models.Sequential([

    layers.Input(shape=(224, 224, 3)),

    layers.Conv2D(32, (3,3), activation="relu"),
    layers.MaxPooling2D(),

    layers.Conv2D(64, (3,3), activation="relu"),
    layers.MaxPooling2D(),

    layers.Conv2D(128, (3,3), activation="relu"),
    layers.MaxPooling2D(),

    layers.Flatten(),

    layers.Dense(256, activation="relu"),
    layers.Dropout(0.5),

    layers.Dense(len(class_names), activation="softmax")
])

# -----------------------------
# Compile Model
# -----------------------------
model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

# -----------------------------
# Model Summary
# -----------------------------
model.summary()

# -----------------------------
# Train Model
# -----------------------------

checkpoint = ModelCheckpoint(
    "model/checkpoint.keras",
    save_best_only=True,
    monitor="val_accuracy"
)

history = model.fit(
    train_dataset,
    validation_data=validation_dataset,
    epochs=10,
    callbacks=[checkpoint]
)

# -----------------------------
# Save Model
# -----------------------------
os.makedirs("model", exist_ok=True)

model.save("model/plant_disease_model.keras")

print("\n==============================")
print("Model Training Completed!")
print("Model Saved Successfully")
print("Location: model/plant_disease_model.keras")
print("==============================")