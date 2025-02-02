# -*- coding: utf-8 -*-
"""26012025 nih CLASSIFICATION IMAGE.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1yrjWFZx11gsDEV9Sg0hURXRhiCrMKm2L
"""

import random
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import tensorflow as tf
import numpy as np
import pandas as pd
import os
import cv2
from google.colab import drive

# Mount Google Drive
drive.mount('/content/drive')

# Paths
image_folder = '/content/drive/My Drive/IMAGE CLASSIFICATION PNEUMONIA/'
csv_file_path = '/content/drive/My Drive/IMAGE CLASSIFICATION PNEUMONIA/Images Label.csv'

# Load and preprocess images
def load_images_from_csv(csv_df, image_folder, target_size=(224, 224)):
    images = []
    labels = []
    missing_images = 0

    all_image_paths = []
    for root, _, files in os.walk(image_folder):
        for file in files:
            if file.endswith(('.png', '.jpg', '.jpeg')):
                all_image_paths.append(os.path.join(root, file))

    for _, row in csv_df.iterrows():
        image_name = row['Image Index']
        label = row['Label']
        matching_path = next((path for path in all_image_paths if os.path.basename(path) == image_name), None)

        if matching_path:
            try:
                img = cv2.imread(matching_path)
                if img is not None:
                    img = cv2.resize(img, target_size)
                    img = img / 255.0
                    images.append(img)
                    labels.append(label)
                else:
                    print(f"Failed to load image: {matching_path}")
            except Exception as e:
                print(f"Error processing image {matching_path}: {e}")
        else:
            missing_images += 1
            if missing_images <= 10:
                print(f"Image not found: {image_name}")
            elif missing_images == 11:
                print("... [More missing images not shown]")

    print(f"Total missing images: {missing_images}")
    return np.array(images), np.array(labels)

# Load the CSV file
labels_df = pd.read_csv(csv_file_path)
labels_df = labels_df[labels_df['Finding Labels'].str.contains('Pneumonia', case=False, na=False)]
print(f"Total samples with 'Pneumonia': {len(labels_df)}")

images, labels = load_images_from_csv(labels_df, image_folder)
print(f"Images loaded: {len(images)}, Labels loaded: {len(labels)}")

if images.shape[0] == 0 or labels.shape[0] == 0:
    raise ValueError("No data loaded. Please check the dataset path and CSV file.")

# Define DenseNet-121 Model
def create_densenet_model(input_shape=(224, 224, 3), dropout_rate=0.3, learning_rate=1e-3):
    base_model = tf.keras.applications.DenseNet121(weights='imagenet', include_top=False, input_shape=input_shape)
    x = base_model.output
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(dropout_rate)(x)
    x = tf.keras.layers.Dense(256, activation='relu')(x)
    x = tf.keras.layers.Dropout(dropout_rate)(x)
    output = tf.keras.layers.Dense(1, activation='sigmoid')(x)  # Binary classification output

    model = tf.keras.Model(inputs=base_model.input, outputs=output)

    model.compile(
        loss="binary_crossentropy",
        optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
        metrics=["accuracy", tf.keras.metrics.Precision(), tf.keras.metrics.Recall()]
    )
    return model

# Define hyperparameter search space
search_space = {
    "input_shape": [(224, 224, 3)],
    "dropout_rate": [0.2, 0.3, 0.4],
    "learning_rate": [1e-3, 1e-4, 1e-5]
}

# Hyperparameter tuning
kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
n_trials = 10
best_model = None
best_score = -np.inf
best_params = None

print("Starting custom hyperparameter search...")

for trial in range(n_trials):
    print(f"\nTrial {trial + 1}/{n_trials}")
    params = {key: random.choice(values) for key, values in search_space.items()}  # Use random.choice
    print("Trial Parameters:", params)

    fold_scores = []
    for train_idx, test_idx in kf.split(images, labels):
        X_train, X_test = images[train_idx], images[test_idx]
        y_train, y_test = labels[train_idx], labels[test_idx]
        model = create_densenet_model(**params)
        model.fit(X_train, y_train, epochs=5, batch_size=32, verbose=0)
        y_pred_probs = model.predict(X_test)
        y_pred = (y_pred_probs > 0.5).astype(int)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=1)
        recall = recall_score(y_test, y_pred, zero_division=1)
        f1 = f1_score(y_test, y_pred, zero_division=1)
        fold_scores.append((accuracy, precision, recall, f1))

    mean_scores = np.mean(fold_scores, axis=0)
    print(f"Trial {trial + 1} Mean Scores - Accuracy: {mean_scores[0]:.4f}, Precision: {mean_scores[1]:.4f}, Recall: {mean_scores[2]:.4f}, F1: {mean_scores[3]:.4f}")

    if mean_scores[3] > best_score:  # Optimise for F1-score
        best_score = mean_scores[3]
        best_model = model
        best_params = params

print("\nHyperparameter Search Completed")
print("Best Hyperparameters:", best_params)
print(f"Best F1-Score: {best_score:.4f}")

import random
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import tensorflow as tf
import numpy as np
import pandas as pd
import os
import cv2
from skimage import exposure, filters
from sklearn.decomposition import PCA
from google.colab import drive

# Mount Google Drive
drive.mount('/content/drive')

# Paths
image_folder = '/content/drive/My Drive/IMAGE CLASSIFICATION PNEUMONIA/'
csv_file_path = '/content/drive/My Drive/IMAGE CLASSIFICATION PNEUMONIA/Images Label.csv'

# Load and preprocess images
def preprocess_image(image_path, target_size=(224, 224)):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)  # Convert to grayscale
    if img is None:
        return None

    img = cv2.resize(img, target_size)

    # Apply CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img = clahe.apply(img)

    # Apply Contrast Enhancement (Gamma Correction)
    gamma = 1.2  # Tunable hyperparameter
    img = exposure.adjust_gamma(img, gamma)

    # Apply Otsu's Thresholding
    threshold = filters.threshold_otsu(img)
    img = (img > threshold).astype(np.uint8) * 255

    return img

# Load dataset
def load_images_from_csv(csv_df, image_folder):
    images = []
    labels = []

    all_image_paths = [os.path.join(root, file) for root, _, files in os.walk(image_folder) for file in files if file.endswith(('.png', '.jpg', '.jpeg'))]

    for _, row in csv_df.iterrows():
        image_name = row['Image Index']
        label = row['Label']
        matching_path = next((path for path in all_image_paths if os.path.basename(path) == image_name), None)

        if matching_path:
            preprocessed_img = preprocess_image(matching_path)
            if preprocessed_img is not None:
                images.append(preprocessed_img)
                labels.append(label)

    return np.array(images), np.array(labels)

# Load images and labels
labels_df = pd.read_csv(csv_file_path)
labels_df = labels_df[labels_df['Finding Labels'].str.contains('Pneumonia', case=False, na=False)]
images, labels = load_images_from_csv(labels_df, image_folder)

# Feature Extraction using PCA only
def extract_features(images, n_components=50):
    images_flattened = images.reshape(images.shape[0], -1)  # Flatten images
    pca = PCA(n_components=n_components)  # Reduce to 50 principal components
    images_pca = pca.fit_transform(images_flattened)
    return images_pca

features = extract_features(images, n_components=50)
labels = labels.ravel()  # Ensure labels are 1D

print("New feature shape:", features.shape)  # Expected shape (num_samples, 50)
print("Labels shape:", labels.shape)  # Expected shape (num_samples,)

# Define Model (Using a Fully Connected Network)
def create_model(input_shape=(100,), dropout_rate=0.3, learning_rate=1e-3):
    inputs = tf.keras.Input(shape=input_shape)

    x = tf.keras.layers.Dense(512, activation='relu')(inputs)
    x = tf.keras.layers.BatchNormalization()(x)  # Normalize activations
    x = tf.keras.layers.Dropout(dropout_rate)(x)

    x = tf.keras.layers.Dense(256, activation='relu')(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(dropout_rate)(x)

    x = tf.keras.layers.Dense(128, activation='relu')(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(dropout_rate)(x)

    output = tf.keras.layers.Dense(1, activation='sigmoid')(x)

    model = tf.keras.Model(inputs=inputs, outputs=output)
    model.compile(loss="binary_crossentropy",
                  optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
                  metrics=["accuracy", tf.keras.metrics.Precision(), tf.keras.metrics.Recall()])
    return model


# Cross-validation
kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
n_trials = 10
best_model = None
best_score = -np.inf
best_params = None

for trial in range(n_trials):
    params = {"dropout_rate": random.choice([0.2, 0.3, 0.4]), "learning_rate": random.choice([1e-3, 1e-4, 1e-5])}
    fold_scores = []

    for train_idx, test_idx in kf.split(features, labels):
        X_train, X_test = features[train_idx], features[test_idx]
        y_train, y_test = labels[train_idx], labels[test_idx]

        model = create_model(input_shape=(50,), **params)
        model.fit(X_train, y_train, epochs=5, batch_size=32, verbose=0)
        y_pred_probs = model.predict(X_test)
        y_pred = (y_pred_probs > 0.5).astype(int)

        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=1)
        recall = recall_score(y_test, y_pred, zero_division=1)
        f1 = f1_score(y_test, y_pred, zero_division=1)
        fold_scores.append((accuracy, precision, recall, f1))

    mean_scores = np.mean(fold_scores, axis=0)
    if mean_scores[3] > best_score:  # Optimise for F1-score
        best_score = mean_scores[3]
        best_model = model
        best_params = params

print("\nHyperparameter Search Completed")
print("Best Hyperparameters:", best_params)
print(f"Best F1-Score: {best_score:.4f}")

#with smote
import random
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import tensorflow as tf
import numpy as np
import pandas as pd
import os
import cv2
from skimage import exposure, filters
from sklearn.decomposition import PCA
from google.colab import drive
from imblearn.over_sampling import SMOTE

# Mount Google Drive
drive.mount('/content/drive')

# Paths
image_folder = '/content/drive/My Drive/IMAGE CLASSIFICATION PNEUMONIA/'
csv_file_path = '/content/drive/My Drive/IMAGE CLASSIFICATION PNEUMONIA/Images Label.csv'

# Load and preprocess images
def preprocess_image(image_path, target_size=(224, 224)):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)  # Convert to grayscale
    if img is None:
        return None

    img = cv2.resize(img, target_size)

    # Apply CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img = clahe.apply(img)

    # Apply Contrast Enhancement (Gamma Correction)
    gamma = 1.2  # Tunable hyperparameter
    img = exposure.adjust_gamma(img, gamma)

    # Apply Otsu's Thresholding
    threshold = filters.threshold_otsu(img)
    img = (img > threshold).astype(np.uint8) * 255

    return img

# Load dataset
def load_images_from_csv(csv_df, image_folder):
    images = []
    labels = []

    all_image_paths = [os.path.join(root, file) for root, _, files in os.walk(image_folder) for file in files if file.endswith(('.png', '.jpg', '.jpeg'))]

    for _, row in csv_df.iterrows():
        image_name = row['Image Index']
        label = row['Label']
        matching_path = next((path for path in all_image_paths if os.path.basename(path) == image_name), None)

        if matching_path:
            preprocessed_img = preprocess_image(matching_path)
            if preprocessed_img is not None:
                images.append(preprocessed_img)
                labels.append(label)

    return np.array(images), np.array(labels)

# Load images and labels
labels_df = pd.read_csv(csv_file_path)
labels_df = labels_df[labels_df['Finding Labels'].str.contains('Pneumonia', case=False, na=False)]
images, labels = load_images_from_csv(labels_df, image_folder)

# Feature Extraction using PCA only
def extract_features(images, n_components=100):
    images_flattened = images.reshape(images.shape[0], -1)  # Flatten images
    pca = PCA(n_components=n_components)  # Reduce to 100 principal components
    images_pca = pca.fit_transform(images_flattened)
    return images_pca

features = extract_features(images, n_components=100)
labels = labels.ravel()  # Ensure labels are 1D

print("New feature shape:", features.shape)  # Expected shape (num_samples, 100)
print("Labels shape:", labels.shape)  # Expected shape (num_samples,)

# Apply SMOTE for class balancing
smote = SMOTE()
features_resampled, labels_resampled = smote.fit_resample(features, labels)

print("After SMOTE - Features shape:", features_resampled.shape)
print("After SMOTE - Labels shape:", labels_resampled.shape)

# Define an improved Model
def create_model(input_shape=(100,), dropout_rate=0.3, learning_rate=1e-3):
    inputs = tf.keras.Input(shape=input_shape)

    x = tf.keras.layers.Dense(512)(inputs)
    x = tf.keras.layers.LeakyReLU(alpha=0.01)(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(dropout_rate)(x)

    x = tf.keras.layers.Dense(256)(x)
    x = tf.keras.layers.LeakyReLU(alpha=0.01)(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(dropout_rate)(x)

    x = tf.keras.layers.Dense(128)(x)
    x = tf.keras.layers.LeakyReLU(alpha=0.01)(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(dropout_rate)(x)

    output = tf.keras.layers.Dense(1, activation='sigmoid')(x)

    model = tf.keras.Model(inputs=inputs, outputs=output)
    model.compile(loss="binary_crossentropy",
                  optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
                  metrics=["accuracy", tf.keras.metrics.Precision(), tf.keras.metrics.Recall()])
    return model

# Cross-validation
kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
n_trials = 10
best_model = None
best_score = -np.inf
best_params = None

for trial in range(n_trials):
    params = {"dropout_rate": random.choice([0.2, 0.3, 0.4]), "learning_rate": random.choice([1e-3, 1e-4, 1e-5])}
    fold_scores = []

    for train_idx, test_idx in kf.split(features_resampled, labels_resampled):
        X_train, X_test = features_resampled[train_idx], features_resampled[test_idx]
        y_train, y_test = labels_resampled[train_idx], labels_resampled[test_idx]

        model = create_model(input_shape=(100,), **params)
        model.fit(X_train, y_train, epochs=30, batch_size=32, verbose=0)
        y_pred_probs = model.predict(X_test)
        y_pred = (y_pred_probs > 0.5).astype(int)

        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=1)
        recall = recall_score(y_test, y_pred, zero_division=1)
        f1 = f1_score(y_test, y_pred, zero_division=1)
        fold_scores.append((accuracy, precision, recall, f1))

    mean_scores = np.mean(fold_scores, axis=0)
    if mean_scores[3] > best_score:  # Optimise for F1-score
        best_score = mean_scores[3]
        best_model = model
        best_params = params

# Print final metrics
print("\nHyperparameter Search Completed")
print("Best Hyperparameters:", best_params)
print(f"Best F1-Score: {best_score:.4f}")

# Evaluate best model on full dataset
y_pred_probs = best_model.predict(features_resampled)
y_pred = (y_pred_probs > 0.5).astype(int)

precision = precision_score(labels_resampled, y_pred, zero_division=1)
recall = recall_score(labels_resampled, y_pred, zero_division=1)
f1 = f1_score(labels_resampled, y_pred, zero_division=1)

print(f"Final Model Precision: {precision:.4f}")
print(f"Final Model Recall: {recall:.4f}")
print(f"Final Model F1-Score: {f1:.4f}")

#without smote
import random
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import tensorflow as tf
import numpy as np
import pandas as pd
import os
import cv2
from skimage import exposure, filters
from sklearn.decomposition import PCA
from google.colab import drive
from collections import Counter

# Mount Google Drive
drive.mount('/content/drive')

# Paths
image_folder = '/content/drive/My Drive/IMAGE CLASSIFICATION PNEUMONIA/'
csv_file_path = '/content/drive/My Drive/IMAGE CLASSIFICATION PNEUMONIA/Images Label.csv'

# Load and preprocess images
def preprocess_image(image_path, target_size=(224, 224)):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)  # Convert to grayscale
    if img is None:
        return None

    img = cv2.resize(img, target_size)

    # Apply CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img = clahe.apply(img)

    # Apply Contrast Enhancement (Gamma Correction)
    gamma = 1.2  # Tunable hyperparameter
    img = exposure.adjust_gamma(img, gamma)

    # Apply Otsu's Thresholding
    threshold = filters.threshold_otsu(img)
    img = (img > threshold).astype(np.uint8) * 255

    return img

# Load dataset
def load_images_from_csv(csv_df, image_folder):
    images = []
    labels = []

    all_image_paths = [os.path.join(root, file) for root, _, files in os.walk(image_folder) for file in files if file.endswith(('.png', '.jpg', '.jpeg'))]

    for _, row in csv_df.iterrows():
        image_name = row['Image Index']
        label = row['Label']
        matching_path = next((path for path in all_image_paths if os.path.basename(path) == image_name), None)

        if matching_path:
            preprocessed_img = preprocess_image(matching_path)
            if preprocessed_img is not None:
                images.append(preprocessed_img)
                labels.append(label)

    return np.array(images), np.array(labels)

# Load images and labels
labels_df = pd.read_csv(csv_file_path)
labels_df = labels_df[labels_df['Finding Labels'].str.contains('Pneumonia', case=False, na=False)]
images, labels = load_images_from_csv(labels_df, image_folder)

# Feature Extraction using PCA only
def extract_features(images, n_components=100):
    images_flattened = images.reshape(images.shape[0], -1)  # Flatten images
    pca = PCA(n_components=n_components)  # Reduce to 100 principal components
    images_pca = pca.fit_transform(images_flattened)
    return images_pca

features = extract_features(images, n_components=100)
labels = labels.ravel()  # Ensure labels are 1D

print("New feature shape:", features.shape)  # Expected shape (num_samples, 100)
print("Labels shape:", labels.shape)  # Expected shape (num_samples,)

# Compute Class Weights (to handle imbalance)
class_counts = Counter(labels)
total_samples = sum(class_counts.values())
class_weights = {cls: total_samples / (len(class_counts) * count) for cls, count in class_counts.items()}

print("Class Weights:", class_weights)

# Define an improved Model with class weighting
def create_model(input_shape=(100,), dropout_rate=0.3, learning_rate=1e-3):
    inputs = tf.keras.Input(shape=input_shape)

    x = tf.keras.layers.Dense(512)(inputs)
    x = tf.keras.layers.LeakyReLU(alpha=0.01)(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(dropout_rate)(x)

    x = tf.keras.layers.Dense(256)(x)
    x = tf.keras.layers.LeakyReLU(alpha=0.01)(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(dropout_rate)(x)

    x = tf.keras.layers.Dense(128)(x)
    x = tf.keras.layers.LeakyReLU(alpha=0.01)(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(dropout_rate)(x)

    output = tf.keras.layers.Dense(1, activation='sigmoid')(x)

    model = tf.keras.Model(inputs=inputs, outputs=output)
    model.compile(loss="binary_crossentropy",
                  optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
                  metrics=["accuracy", tf.keras.metrics.Precision(), tf.keras.metrics.Recall()])
    return model

# Cross-validation
kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
n_trials = 10
best_model = None
best_score = -np.inf
best_params = None

for trial in range(n_trials):
    params = {"dropout_rate": random.choice([0.2, 0.3, 0.4]), "learning_rate": random.choice([1e-3, 1e-4, 1e-5])}
    fold_scores = []

    for train_idx, test_idx in kf.split(features, labels):
        X_train, X_test = features[train_idx], features[test_idx]
        y_train, y_test = labels[train_idx], labels[test_idx]

        model = create_model(input_shape=(100,), **params)
        model.fit(X_train, y_train, epochs=30, batch_size=32, verbose=0, class_weight=class_weights)
        y_pred_probs = model.predict(X_test)
        y_pred = (y_pred_probs > 0.5).astype(int)

        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=1)
        recall = recall_score(y_test, y_pred, zero_division=1)
        f1 = f1_score(y_test, y_pred, zero_division=1)
        fold_scores.append((accuracy, precision, recall, f1))

    mean_scores = np.mean(fold_scores, axis=0)
    if mean_scores[3] > best_score:  # Optimise for F1-score
        best_score = mean_scores[3]
        best_model = model
        best_params = params

# Print final metrics
print("\nHyperparameter Search Completed")
print("Best Hyperparameters:", best_params)
print(f"Best F1-Score: {best_score:.4f}")

# Evaluate best model on full dataset
y_pred_probs = best_model.predict(features)
y_pred = (y_pred_probs > 0.5).astype(int)

precision = precision_score(labels, y_pred, zero_division=1)
recall = recall_score(labels, y_pred, zero_division=1)
f1 = f1_score(labels, y_pred, zero_division=1)

print(f"Final Model Precision: {precision:.4f}")
print(f"Final Model Recall: {recall:.4f}")
print(f"Final Model F1-Score: {f1:.4f}")