# HCR4 - Handwriting Recognition for Medical Prescriptions

HCR4 est un système d'extraction et de reconnaissance d'écriture manuscrite (HTR/OCR) appliqué aux ordonnances médicales. L'application est basée sur **Streamlit** pour l'interface utilisateur, intègre un pipeline d'Intelligence Artificielle utilisant **TrOCR (Vision Transformers)**, et s'appuie sur une base de données **MongoDB**.

Ce guide est destiné aux collaborateurs souhaitant cloner et déployer l'application en local.

## Prérequis

- **Python 3.9+**
- **MongoDB** (Le projet inclut des scripts pour configurer un Replica Set)
- **Git**

## Installation en Local

Suivez ces étapes pour configurer et lancer le projet sur votre machine locale :

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-utilisateur/HCR-annotation.git
cd HCR-annotation
# ou cd HCR4 selon le nom de votre dossier local
```

### 2. Créer et activer un environnement virtuel (Recommandé)

Il est fortement recommandé d'utiliser un environnement virtuel pour isoler les dépendances du projet.

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances

Installez toutes les bibliothèques requises à l'aide de `pip` :

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configurer et Lancer la Base de Données MongoDB

Le projet utilise MongoDB en mode *Replica Set*. Les scripts nécessaires sont dans le dossier `database`.

```bash
cd database

# Lancer l'initialisation complète de la base de données (Replica Set + Init DB)
# Ce script peut demander des privilèges sudo
sudo bash run_all.sh
```

*(Note : Si MongoDB n'est pas encore installé sur votre système, vous pouvez exécuter au préalable le script `sudo bash install_mongodb.sh` situé dans le même dossier).*

### 5. Initialiser les Identifiants par Défaut (Seed)

Une fois la base de données opérationnelle, il est nécessaire de créer les utilisateurs de base et de hacher les mots de passe.

```bash
# Retourner à la racine du projet
cd ..

# Exécuter le script de remplissage
python database/seed_passwords.py
```

Vous aurez accès aux **identifiants par défaut** suivants :
- **Admin** : `admin@hcr4.sn` / `admin123`
- **Médecin** : `m.diallo@hopital.sn` / `pass123`
- **Patient** : `a.sow@email.sn` / `pass123`
- **Pharmacie** : `contact@pharma-centrale.sn` / `pharma123`

## Lancer l'Application

Vous pouvez maintenant démarrer l'application Streamlit. Depuis la racine du projet, exécutez simplement :

```bash
python run.py
```

*(Il est également possible de lancer l'application via `streamlit run frontend/app.py`)*

L'application sera accessible depuis votre navigateur à l'adresse : [http://localhost:8501](http://localhost:8501).

## Structure du Projet

- `backend/` : Logique interne et pipeline d'intelligence artificielle (fichiers de fine-tuning TrOCR, augmentation de données, etc.).
- `frontend/` : Interface utilisateur Streamlit, composants et pages de l'application.
- `database/` : Scripts shell de configuration MongoDB et scripts d'amorçage Python.
- `data/` : Dossier contenant les données brutes, les références (ex: `meds_reference.csv`) et potentiellement les modèles locaux.
- `evaluation/` : Scripts de test et calculs de métriques de performance.
- `run.py` : Script point d'entrée pour démarrer l'application.
- `requirements.txt` : Liste des dépendances Python du projet.
