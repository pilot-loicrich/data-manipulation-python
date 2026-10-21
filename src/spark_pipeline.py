"""PySpark pipeline for the retail sales project.

Run from the project root with:
    spark-submit src/spark_pipeline.py

The source CSV files are generated for the PMD exercises. The output is a
Parquet dataset partitioned by year under data/processed/ventes_projet_spark.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql import Window
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "ventes_projet_spark"

SALES_SCHEMA = StructType([
    StructField("id_commande", StringType(), True),
    StructField("date_commande", StringType(), True),
    StructField("id_client", StringType(), True),
    StructField("id_produit", StringType(), True),
    StructField("id_magasin", StringType(), True),
    StructField("quantite", IntegerType(), True),
    StructField("prix_unitaire", StringType(), True),
    StructField("remise_pct", DoubleType(), True),
    StructField("canal", StringType(), True),
    StructField("statut", StringType(), True),
    StructField("ville_livraison", StringType(), True),
])


def _normalized_text(column_name: str):
    """Return a Spark expression that normalizes common French text variants."""
    value = F.lower(F.regexp_replace(F.trim(F.col(column_name)), r"\s+", " "))
    for accented, plain in [
        ("é", "e"), ("è", "e"), ("ê", "e"), ("à", "a"), ("â", "a"),
        ("î", "i"), ("ï", "i"), ("ô", "o"), ("ö", "o"), ("ù", "u"),
        ("û", "u"), ("ü", "u"), ("ç", "c"),
    ]:
        value = F.regexp_replace(value, accented, plain)
    return value


def clean_sales(df: DataFrame) -> DataFrame:
    """Clean sales while keeping all transformations distributed in Spark."""
    price_text = F.regexp_replace(
        F.regexp_replace(F.trim(F.col("prix_unitaire")), r"(?i)\s*EUR$", ""),
        ",",
        ".",
    )
    parsed_date = F.coalesce(
        F.to_timestamp("date_commande", "yyyy-MM-dd"),
        F.to_timestamp("date_commande", "dd/MM/yyyy"),
        F.to_timestamp("date_commande", "dd-MM-yyyy"),
        F.to_timestamp("date_commande", "yyyy/MM/dd HH:mm"),
        F.to_timestamp("date_commande", "dd MMM yyyy"),
    )

    return (
        df.withColumn("prix_unitaire", price_text.cast("double"))
        .withColumn("date_commande", parsed_date)
        .withColumn("canal", _normalized_text("canal"))
        .withColumn("statut", _normalized_text("statut"))
        .withColumn("ville_livraison", _normalized_text("ville_livraison"))
        .dropDuplicates()
        .filter(F.col("date_commande").isNotNull())
        .filter(F.col("quantite") > 0)
        .na.fill({"remise_pct": 0.0})
        .withColumn(
            "montant",
            F.round(
                F.col("quantite")
                * F.col("prix_unitaire")
                * (1 - F.col("remise_pct") / 100),
                2,
            ),
        )
        .withColumn("annee", F.year("date_commande"))
        .withColumn("mois", F.month("date_commande"))
        .withColumn(
            "ca_realise",
            F.when(F.col("statut") == "livre", F.col("montant")).otherwise(0.0),
        )
    )


def create_spark_session(app_name: str = "PMD-projet-ventes") -> SparkSession:
    """Create a Spark session tuned for a local learning machine."""
    return (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "16")
        .config("spark.sql.ansi.enabled", "false")
        .getOrCreate()
    )


def build_project_dataframe(
    spark: SparkSession,
    sales_path: str | Path = RAW_DIR / "ventes_brutes.csv",
    products_path: str | Path = RAW_DIR / "produits.csv",
    stores_path: str | Path = RAW_DIR / "magasins.csv",
) -> DataFrame:
    """Clean sales, join small dimensions, and add analysis-ready date fields."""
    sales = spark.read.csv(str(sales_path), header=True, schema=SALES_SCHEMA)
    products = spark.read.option("header", True).option("inferSchema", True).csv(
        str(products_path)
    )
    stores = spark.read.option("header", True).option("inferSchema", True).csv(
        str(stores_path)
    )
    product_window = Window.partitionBy("sous_categorie")
    products = products.withColumn(
        "cout_achat",
        F.coalesce(
            F.col("cout_achat"),
            F.expr("percentile_approx(cout_achat, 0.5)").over(product_window),
        ),
    )

    return (
        clean_sales(sales)
        .join(F.broadcast(products), on="id_produit", how="left")
        .join(F.broadcast(stores), on="id_magasin", how="left")
        .withColumn(
            "marge_estimee",
            F.round(
                F.col("ca_realise") - F.col("quantite") * F.col("cout_achat"),
                2,
            ),
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sales", default=str(RAW_DIR / "ventes_brutes.csv"))
    parser.add_argument("--products", default=str(RAW_DIR / "produits.csv"))
    parser.add_argument("--stores", default=str(RAW_DIR / "magasins.csv"))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")
    try:
        result = build_project_dataframe(
            spark, args.sales, args.products, args.stores
        )
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.write.mode("overwrite").partitionBy("annee").parquet(str(output_path))
        print(f"Sortie Parquet : {output_path}")
        print("Ventes livrées par région et catégorie :")
        (result.groupBy("region", "categorie")
         .agg(F.round(F.sum("ca_realise"), 2).alias("ca_livre"))
         .orderBy(F.desc("ca_livre"))
         .show(30, truncate=False))
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
