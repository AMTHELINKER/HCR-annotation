import os
import cv2
import csv
import numpy as np
import random

DATASET_DIR = "/home/am/AM/HCR4/backend/ai/finetuning/dataset"
IMAGES_DIR = os.path.join(DATASET_DIR, "images")
TRAIN_CSV = os.path.join(DATASET_DIR, "_train_split.csv")
ANNO_CSV = os.path.join(DATASET_DIR, "annotations.csv")

# ==========================================
# Augmentation functions using OpenCV
# ==========================================

def augment_blur(img):
    """Applique un flou gaussien aléatoire pour simuler une mauvaise mise au point."""
    k = random.choice([3, 5])
    return cv2.GaussianBlur(img, (k, k), 0)

def augment_brightness_contrast(img):
    """Modifie le contraste et la luminosité."""
    alpha = random.uniform(0.7, 1.3) # Contraste
    beta = random.uniform(-30, 30)   # Luminosité
    return cv2.convertScaleAbs(img, alpha=alpha, beta=beta)

def augment_rotation(img):
    """Applique une légère rotation aléatoire (-5 à 5 degrés)."""
    h, w = img.shape[:2]
    angle = random.uniform(-5, 5)
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    # Remplir les bords avec du blanc (255, 255, 255)
    return cv2.warpAffine(img, M, (w, h), borderValue=(255, 255, 255))

def augment_morphology(img):
    """Simule une encre plus épaisse ou plus fine (érosion / dilatation)."""
    kernel = np.ones((2, 2), np.uint8)
    if random.choice([True, False]):
        # Dilatation = lignes plus fines (car le fond blanc s'étend)
        return cv2.dilate(img, kernel, iterations=1)
    else:
        # Érosion = lignes plus épaisses (car le texte noir s'étend)
        return cv2.erode(img, kernel, iterations=1)

def augment_noise(img):
    """Ajoute du bruit poivre et sel."""
    row, col, ch = img.shape
    s_vs_p = 0.5
    amount = 0.01
    out = np.copy(img)
    # Salt mode
    num_salt = np.ceil(amount * img.size * s_vs_p)
    coords = [np.random.randint(0, i - 1, int(num_salt)) for i in img.shape]
    out[tuple(coords)] = 255
    # Pepper mode
    num_pepper = np.ceil(amount * img.size * (1. - s_vs_p))
    coords = [np.random.randint(0, i - 1, int(num_pepper)) for i in img.shape]
    out[tuple(coords)] = 0
    return out

# Liste des pipelines d'augmentation (chaque fonction retourne une image modifiée)
def apply_augmentations(img):
    """Génère 2 variantes d'une image pour doubler le dataset sans biaiser la distribution."""
    variants = []
    
    # Variante 1: Morphologie (Encre) + Rotation légère
    img1 = augment_morphology(img)
    img1 = augment_rotation(img1)
    variants.append(("augA", img1))
    
    # Variante 2: Flou ou Bruit + Contraste
    img2 = augment_blur(img) if random.choice([True, False]) else augment_noise(img)
    img2 = augment_brightness_contrast(img2)
    variants.append(("augB", img2))
    
    return variants

# ==========================================
# Main execution
# ==========================================

def main():
    # 1. Charger le train split
    train_data = []
    with open(TRAIN_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            train_data.append(row)
            
    print(f"Nombre total d'images dans le train set: {len(train_data)}")
    
    # Augmenter TOUTES les images pour maintenir la distribution des mots équilibrée
    print(f"Cibles pour augmentation : TOUT le dataset d'entraînement ({len(train_data)} images)")
    
    new_train_entries = []
    
    for row in train_data:
        file_name = row["file_name"]
        text = row["text"]
        img_path = os.path.join(IMAGES_DIR, file_name)
        
        if not os.path.exists(img_path):
            continue
            
        img = cv2.imread(img_path)
        if img is None:
            continue
            
        # Générer les augmentations
        variants = apply_augmentations(img)
        
        for prefix, aug_img in variants:
            new_file_name = f"{prefix}_{file_name}"
            new_img_path = os.path.join(IMAGES_DIR, new_file_name)
            
            # Sauvegarder l'image augmentée
            cv2.imwrite(new_img_path, aug_img)
            
            # Ajouter aux nouvelles entrées
            new_train_entries.append({
                "file_name": new_file_name,
                "text": text
            })
            
    print(f"Génération terminée. {len(new_train_entries)} images ajoutées.")
    
    # 3. Mettre à jour le train_split.csv
    with open(TRAIN_CSV, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file_name", "text"])
        for entry in new_train_entries:
            writer.writerow(entry)
            
    # 4. Mettre à jour annotations.csv global
    with open(ANNO_CSV, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file_name", "text"])
        for entry in new_train_entries:
            writer.writerow(entry)
            
    print(f"Mise à jour de {TRAIN_CSV} et {ANNO_CSV} réussie.")

if __name__ == "__main__":
    main()
