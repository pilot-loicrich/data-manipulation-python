# Module PMD — Préparation et Manipulation de Données (M1)

Ce projet rassemble les ateliers pratiques et pipelines de données du module PMD.

## Description
Le projet vise à explorer, nettoyer et transformer des jeux de données de ventes et de capteurs présentant des anomalies intentionnelles (valeurs manquantes, formats hétérogènes, doublons, casse instable).

## Installation
1. Cloner ou ouvrir le projet dans votre terminal.
2. Créer l'environnement virtuel : `python -m venv .venv`
3. Activer l'environnement :
   - Windows : `.\.venv\Scripts\Activate.ps1`
   - Linux/macOS : `source .venv/bin/activate`
4. Installer les dépendances : `pip install -r requirements.txt`

## Données
- Données brutes : `data/raw/` (lecture seule, générées via `python src/generate_data.py`).
- Données transformées : `data/processed/` (formats Parquet et CSV prêts pour l'analyse).
- Code réutilisable : `src/` (`generate_data.py`, `exploration.py`).
