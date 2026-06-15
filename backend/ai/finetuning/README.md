# Finetuning du Modèle TrOCR

Ce dossier est dédié à l'entraînement (fine-tuning) du modèle TrOCR sur votre propre base de données d'ordonnances médicales.

## Structure attendue des données

Veuillez placer votre dataset dans le sous-dossier `dataset/` :

```text
finetuning/
├── dataset/
│   ├── images/          # Placez ici toutes vos images recadrées (lignes d'ordonnances)
│   └── annotations.csv  # Votre fichier CSV liant les images au texte
├── dataset.py           # Script de chargement des données (PyTorch Dataset)
├── train.py             # Script principal d'entraînement
└── README.md            # Ce fichier
```

### Format du fichier `annotations.csv`

Le fichier CSV doit contenir au moins deux colonnes : le nom du fichier image et le texte manuscrit correspondant (le médicament).

Exemple :
```csv
file_name,text
image_001.jpg,Doliprane 1000mg
image_002.jpg,Amoxicilline 500
image_003.jpg,Ibuprofene 400mg
```

## Utilisation

Une fois vos images et votre CSV en place, vous pouvez lancer l'entraînement en exécutant le script `train.py` :

```bash
cd backend/ai/finetuning
python train.py
```
