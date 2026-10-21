"""PySpark pipeline for group 01's library activity project.

Run from the project root with:
    spark-submit src/library_pipeline.py

The output is a Parquet dataset partitioned by year under data/processed/.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import Window
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)


ROOT = Path(__file__).resolve().parents[1]
GROUP_DIR = ROOT / "data" / "groupe_01_bibliotheque" / "groupe_01_bibliotheque"
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "bibliotheque_projet_spark"

BORROW_SCHEMA = StructType([
    StructField("id_emprunt", StringType(), True),
    StructField("date_evenement", StringType(), True),
    StructField("id_adherent", StringType(), True),
    StructField("id_ouvrage", StringType(), True),
    StructField("id_site", StringType(), True),
    StructField("duree_pret_jours", DoubleType(), True),
    StructField("nb_prolongations", IntegerType(), True),
    StructField("valeur_ouvrage_eur", StringType(), True),
    StructField("mode_emprunt", StringType(), True),
    StructField("statut", StringType(), True),
])


def _normalized_text(column_name: str):
    value = F.lower(F.regexp_replace(F.trim(F.col(column_name)), r"\s+", " "))
    for accented, plain in [
        ("é", "e"), ("è", "e"), ("ê", "e"), ("à", "a"), ("â", "a"),
        ("î", "i"), ("ï", "i"), ("ô", "o"), ("ö", "o"), ("ù", "u"),
        ("û", "u"), ("ü", "u"), ("ç", "c"),
    ]:
        value = F.regexp_replace(value, accented, plain)
    return value


def clean_borrows(df: DataFrame) -> DataFrame:
    """Parse, normalize and validate the loan-event fact table."""
    value_text = F.regexp_replace(
        F.regexp_replace(F.trim(F.col("valeur_ouvrage_eur")), r"(?i)\s*EUR$", ""),
        ",",
        ".",
    )
    parsed_date = F.coalesce(
        F.to_timestamp("date_evenement", "yyyy-MM-dd"),
        F.to_timestamp("date_evenement", "dd/MM/yyyy"),
        F.to_timestamp("date_evenement", "dd-MM-yyyy"),
        F.to_timestamp("date_evenement", "yyyy/MM/dd HH:mm"),
        F.to_timestamp("date_evenement", "dd MMM yyyy"),
    )

    return (
        df.withColumn("date_evenement", parsed_date)
        .withColumn("duree_pret_jours", F.col("duree_pret_jours").cast("double"))
        .withColumn("nb_prolongations", F.col("nb_prolongations").cast("int"))
        .withColumn("valeur_ouvrage_eur", value_text.cast("double"))
        .withColumn("mode_emprunt", _normalized_text("mode_emprunt"))
        .withColumn("statut", _normalized_text("statut"))
        .dropDuplicates()
        .filter(F.col("date_evenement").isNotNull())
        .filter(F.col("duree_pret_jours").isNull() | (F.col("duree_pret_jours") >= 0))
        .withColumn("annee", F.year("date_evenement"))
        .withColumn("mois", F.month("date_evenement"))
        .withColumn("est_en_retard", (F.col("statut") == "en_retard").cast("int"))
        .withColumn("est_perdu", (F.col("statut") == "perdu").cast("int"))
        .withColumn(
            "valeur_perdue_eur",
            F.when(F.col("statut") == "perdu", F.col("valeur_ouvrage_eur"))
             .otherwise(F.lit(0.0)),
        )
    )


def create_spark_session(app_name: str = "PMD-projet-bibliotheque") -> SparkSession:
    return (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "16")
        .config("spark.sql.ansi.enabled", "false")
        .getOrCreate()
    )


def _require_unique_key(dimension: DataFrame, key: str) -> None:
    """Fail early if a dimension cannot support a many-to-one join."""
    has_null_key = dimension.filter(F.col(key).isNull()).limit(1).count() > 0
    has_duplicate_key = (
        dimension.groupBy(key).count().filter(F.col("count") > 1).limit(1).count() > 0
    )
    if has_null_key or has_duplicate_key:
        raise ValueError(f"La clé {key} du référentiel doit être unique et renseignée")


def build_library_dataframe(
    spark: SparkSession,
    group_dir: str | Path = GROUP_DIR,
) -> DataFrame:
    """Clean events and enrich them with book, site and member dimensions."""
    group_dir = Path(group_dir)
    borrows = spark.read.csv(
        str(group_dir / "emprunts.csv"), header=True, schema=BORROW_SCHEMA
    )
    books = spark.read.option("header", True).option("inferSchema", True).csv(
        str(group_dir / "ouvrages.csv")
    )
    sites = spark.read.option("header", True).option("inferSchema", True).csv(
        str(group_dir / "sites.csv")
    ).select(
        "id_site", "nom_site", F.col("ville").alias("ville_site"),
        "region", "capacite",
    )
    members = spark.read.option("header", True).option("inferSchema", True).csv(
        str(group_dir / "adherents.csv")
    ).select(
        "id_adherent", "date_creation", "segment", F.col("ville").alias("ville_adherent"),
        "age",
    )

    for column in ("famille", "sous_famille"):
        books = books.withColumn(column, _normalized_text(column))
    book_median = F.expr("percentile_approx(cout_reference_eur, 0.5)").over(
        Window.partitionBy("sous_famille")
    )
    books = books.withColumn(
        "cout_reference_eur",
        F.coalesce(F.col("cout_reference_eur"), book_median),
    )
    for column in ("region", "ville"):
        sites = sites.withColumn(column, _normalized_text(column))
    members = members.withColumn("segment", _normalized_text("segment"))
    member_median = F.expr("percentile_approx(age, 0.5)").over(
        Window.partitionBy("segment")
    )
    members = members.withColumn("age", F.coalesce(F.col("age"), member_median))

    _require_unique_key(books, "id_ouvrage")
    _require_unique_key(sites, "id_site")
    _require_unique_key(members, "id_adherent")

    return (
        clean_borrows(borrows)
        .join(F.broadcast(books), on="id_ouvrage", how="left")
        .join(F.broadcast(sites), on="id_site", how="left")
        .join(F.broadcast(members), on="id_adherent", how="left")
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group-dir", default=str(GROUP_DIR))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")
    try:
        result = build_library_dataframe(spark, args.group_dir)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.write.mode("overwrite").partitionBy("annee").parquet(str(output_path))
        print(f"Sortie Parquet : {output_path}")
        print("Activité par région et famille d’ouvrage :")
        (result.groupBy("region", "famille")
         .agg(
             F.count("*").alias("emprunts"),
             F.sum("est_en_retard").alias("en_retard"),
             F.sum("est_perdu").alias("perdus"),
             F.round(F.sum("valeur_perdue_eur"), 2).alias("valeur_perdue_eur"),
         )
         .orderBy(F.desc("emprunts"))
         .show(30, truncate=False))
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
