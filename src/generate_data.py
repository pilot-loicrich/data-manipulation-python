import argparse
import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

SEED = 42
RAW_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")

CITIES = ["Paris", "Lyon", "Marseille", "Lille", "Bordeaux", "Nantes", "Toulouse", "Strasbourg"]
REGIONS = {
    "Paris": "Ile-de-France", "Lyon": "Auvergne-Rhone-Alpes", "Marseille": "PACA",
    "Lille": "Hauts-de-France", "Bordeaux": "Nouvelle-Aquitaine", "Nantes": "Pays de la Loire",
    "Toulouse": "Occitanie", "Strasbourg": "Grand Est",
}
CATEGORIES = {
    "Informatique": ["Ordinateur portable", "Ecran", "Clavier", "Souris"],
    "Audio": ["Casque", "Enceinte", "Micro"],
    "Mobilier": ["Bureau", "Chaise", "Lampe"],
    "Accessoire": ["Sacoche", "Cable", "Adaptateur"],
}
DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d %H:%M", "%d %b %Y"]


def messy_case(value, rng):
    """Reproduit la saisie humaine : casse instable et espaces parasites."""
    draw = rng.random()
    if draw < 0.12:
        return value.upper()
    if draw < 0.24:
        return value.lower()
    if draw < 0.32:
        return "  " + value + " "
    return value


def format_date(moment, rng):
    """Renvoie la même date dans l'un des cinq formats rencontrés en production."""
    return moment.strftime(DATE_FORMATS[rng.integers(0, len(DATE_FORMATS))])


def generate_products(rng):
    rows = []
    product_number = 1
    for category, subcategories in CATEGORIES.items():
        for subcategory in subcategories:
            for variant in range(1, 4):
                rows.append({
                    "id_produit": f"P{product_number:04d}",
                    "libelle": f"{subcategory} modele {variant}",
                    "categorie": category,
                    "sous_categorie": subcategory,
                    "cout_achat": float(np.round(rng.uniform(8, 620), 2)),
                })
                product_number += 1

    products = pd.DataFrame(rows)
    missing_index = rng.choice(products.index, size=int(len(products) * 0.03), replace=False)
    products.loc[missing_index, "cout_achat"] = np.nan
    return products


def generate_stores(rng):
    rows = []
    for number, city in enumerate(CITIES, start=1):
        rows.append({
            "id_magasin": f"M{number:02d}",
            "nom_magasin": f"Boutique {city}",
            "ville": city,
            "region": REGIONS[city],
            "surface_m2": int(rng.integers(120, 900)),
        })
    rows.append({
        "id_magasin": "M99", "nom_magasin": "Entrepot central",
        "ville": "Orleans", "region": "Centre-Val de Loire", "surface_m2": 4200,
    })
    return pd.DataFrame(rows)


CHANNELS = ["web", "boutique", "telephone"]
STATUSES = ["livre", "livre", "livre", "livre", "annule", "en_cours", "expedie"]

FIRST_NAMES = [
    "Jean", "Marie", "Pierre", "Sophie", "Lucas", "Emma", "Thomas", "Camille",
    "Nicolas", "Lea", "Alexandre", "Chloe", "Antoine", "Manon", "Julien", "Sarah"
]
LAST_NAMES = [
    "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand",
    "Leroy", "Moreau", "Simon", "Laurent", "Lefebvre", "Michel", "Garcia", "David"
]


def generate_customers(rng, n_customers=3000):
    start = datetime(2019, 1, 1)
    rows = []
    for i in range(1, n_customers + 1):
        fn = rng.choice(FIRST_NAMES)
        ln = rng.choice(LAST_NAMES)
        days_offset = int(rng.integers(0, 1800))
        reg_date = start + timedelta(days=days_offset)
        city = rng.choice(CITIES)
        email = f"{fn.lower()}.{ln.lower()}{i % 50}@example.com"
        if rng.random() < 0.05:
            email = "  " + email
        rows.append({
            "id_client": f"C{i:04d}",
            "nom": ln,
            "prenom": fn,
            "email": email,
            "ville": city,
            "date_inscription": reg_date.strftime("%Y-%m-%d"),
            "segment": rng.choice(["Particulier", "Professionnel", "VIP"], p=[0.75, 0.20, 0.05]),
        })
    return pd.DataFrame(rows)


def generate_sensors(rng):
    rows = []
    start_date = datetime(2023, 1, 1)
    sensor_cities = ["Paris", "Lyon", "Marseille", "Lille", "Bordeaux"]
    for s_id, city in enumerate(sensor_cities, start=1):
        for month in range(12):
            base_temp = 14 + 10 * np.sin((month - 3) * np.pi / 6)
            temp = float(np.round(rng.normal(loc=base_temp, scale=4), 1))
            rows.append({
                "id_capteur": f"CAPT_{s_id:02d}",
                "ville": city,
                "mois": month + 1,
                "date_releve": (start_date + timedelta(days=month * 30)).strftime("%Y-%m-%d"),
                "temperature": temp,
            })
    return pd.DataFrame(rows)


def generate_sales(products, stores, customers, rng, n_sales=17600):
    start = datetime(2021, 1, 1)
    prod_ids = products["id_produit"].tolist()
    cost_lookup = dict(zip(products["id_produit"], products["cout_achat"].fillna(50.0)))
    store_ids = stores["id_magasin"].tolist()
    cust_ids = customers["id_client"].tolist()

    rows = []
    for i in range(1, n_sales + 1):
        pid = rng.choice(prod_ids)
        cid = rng.choice(cust_ids)
        mid = rng.choice(store_ids)
        qty = int(rng.integers(1, 12))
        statut = rng.choice(STATUSES)
        canal = messy_case(rng.choice(CHANNELS), rng)

        base_cost = cost_lookup[pid]
        margin = float(rng.uniform(1.2, 1.8))
        unit_price_val = round(base_cost * margin, 2)

        if rng.random() < 0.25:
            price_str = f"{unit_price_val:.2f}".replace(".", ",") + " EUR"
        else:
            price_str = f"{unit_price_val:.2f}"

        days = int(rng.integers(0, 1095))
        sale_date = start + timedelta(days=days, hours=int(rng.integers(8, 20)), minutes=int(rng.integers(0, 60)))
        date_str = format_date(sale_date, rng)

        if rng.random() < 0.02:
            cid = rng.choice(["", "NC"])
        if rng.random() < 0.015:
            pid = rng.choice(["", "NC"])
        if rng.random() < 0.015:
            mid = rng.choice(["", "NC"])

        rows.append({
            "id_commande": f"CMD{i:06d}",
            "date_commande": date_str,
            "id_client": cid,
            "id_magasin": mid,
            "id_produit": pid,
            "quantite": qty,
            "prix_unitaire": price_str,
            "statut": statut,
            "canal": canal,
        })

    df = pd.DataFrame(rows)

    n_duplicates = int(len(df) * 0.015)
    dup_rows = df.sample(n=n_duplicates, random_state=SEED)
    df = pd.concat([df, dup_rows], ignore_index=True)
    return df


def main():
    parser = argparse.ArgumentParser(description="Générateur de données dégradées pour le module PMD.")
    parser.add_argument("--big", type=int, default=0, help="Générer un fichier volumineux de N lignes.")
    args = parser.parse_args()

    os.makedirs(RAW_DIR, exist_ok=True)
    rng = np.random.default_rng(SEED)

    print("Génération des jeux de données PMD...")

    products = generate_products(rng)
    prod_path = os.path.join(RAW_DIR, "produits.csv")
    products.to_csv(prod_path, index=False)
    print(f"  [OK] {prod_path} ({len(products)} lignes)")

    stores = generate_stores(rng)
    stores_path = os.path.join(RAW_DIR, "magasins.csv")
    stores.to_csv(stores_path, index=False)
    print(f"  [OK] {stores_path} ({len(stores)} lignes)")

    customers = generate_customers(rng, n_customers=3000)
    cust_path = os.path.join(RAW_DIR, "clients.csv")
    customers.to_csv(cust_path, index=False)
    print(f"  [OK] {cust_path} ({len(customers)} lignes)")

    sensors = generate_sensors(rng)
    sensors_path = os.path.join(RAW_DIR, "capteurs.csv")
    sensors.to_csv(sensors_path, index=False)
    print(f"  [OK] {sensors_path} ({len(sensors)} lignes)")

    sales = generate_sales(products, stores, customers, rng, n_sales=17600)
    sales_path = os.path.join(RAW_DIR, "ventes_brutes.csv")
    sales.to_csv(sales_path, index=False)
    print(f"  [OK] {sales_path} ({len(sales)} lignes)")

    sample = sales.head(1000).copy()
    sample_csv_path = os.path.join(RAW_DIR, "ventes_extrait.csv")
    sample_xlsx_path = os.path.join(RAW_DIR, "ventes_extrait.xlsx")
    sample_json_path = os.path.join(RAW_DIR, "ventes_extrait.json")

    sample.to_csv(sample_csv_path, index=False)
    sample.to_excel(sample_xlsx_path, index=False)
    sample.to_json(sample_json_path, orient="records", date_format="iso", indent=2)

    print(f"  [OK] {sample_xlsx_path} (1000 lignes)")
    print(f"  [OK] {sample_json_path} (1000 lignes)")
    print(f"  [OK] {sample_csv_path} (1000 lignes)")

    gitkeep_path = os.path.join(RAW_DIR, ".gitkeep")
    with open(gitkeep_path, "a"):
        pass
    print(f"  [OK] {gitkeep_path}")

    if args.big > 0:
        print(f"Génération du fichier volumineux ({args.big} lignes)...")
        big_sales = generate_sales(products, stores, customers, rng, n_sales=args.big)
        big_path = os.path.join(RAW_DIR, "ventes_volumineux.csv")
        big_sales.to_csv(big_path, index=False)
        print(f"  [OK] {big_path}")

    print("\nToutes les données ont été générées avec succès dans data/raw/ !")


if __name__ == "__main__":
    main()
