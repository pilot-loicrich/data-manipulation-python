"""PySpark pipeline for the group 03 canteen dataset."""
from __future__ import annotations
import argparse
from pathlib import Path
from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

ROOT = Path(__file__).resolve().parents[1]
GROUP_DIR = ROOT / "data" / "groupe_03_cantine" / "groupe_03_cantine"
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "cantine_projet_spark"


def _norm(name: str):
    value = F.lower(F.regexp_replace(F.trim(F.col(name)), r"\s+", " "))
    return F.translate(value, "\u00e9\u00e8\u00ea\u00e0\u00e2\u00ee\u00ef\u00f4\u00f6\u00f9\u00fb\u00fc\u00e7", "eeeaaiioouuuc")


def _unique(dimension: DataFrame, key: str) -> None:
    duplicate = dimension.groupBy(key).count().filter(F.col("count") > 1).limit(1).count()
    null_key = dimension.filter(F.col(key).isNull()).limit(1).count()
    if duplicate or null_key:
        raise ValueError(f"Dimension key must be unique and non-null: {key}")


def build_canteen_dataframe(spark: SparkSession, group_dir: str | Path = GROUP_DIR) -> DataFrame:
    path = Path(group_dir)
    meals = spark.read.option("header", True).option("inferSchema", True).csv(str(path / "repas_servis.csv"))
    menus = spark.read.option("header", True).option("inferSchema", True).csv(str(path / "menus.csv"))
    sites = spark.read.option("header", True).option("inferSchema", True).csv(str(path / "etablissements.csv"))
    diners = spark.read.option("header", True).option("inferSchema", True).csv(str(path / "convives.csv"))
    cost = F.regexp_replace(F.regexp_replace(F.trim(F.col("cout_revient_eur")), r"(?i)\s*EUR$", ""), ",", ".").cast("double")
    meals = (meals
        .withColumn("date_evenement", F.to_date("date_evenement"))
        .withColumn("portions_servies", F.col("portions_servies").cast("double"))
        .withColumn("grammage_g", F.col("grammage_g").cast("double"))
        .withColumn("cout_revient_eur", cost)
        .withColumn("regime", _norm("regime"))
        .withColumn("statut", _norm("statut"))
        .dropDuplicates()
        .filter(F.col("date_evenement").isNotNull())
        .withColumn("annee", F.year("date_evenement"))
        .withColumn("mois", F.month("date_evenement"))
        .withColumn("portions_atypiques", (F.col("portions_servies") == 0) | (F.col("portions_servies") > 10))
        .withColumn("est_consomme", (F.col("statut") == "consomme").cast("int"))
        .withColumn("est_annule", (F.col("statut") == "annule").cast("int"))
        .withColumn("est_non_recupere", (F.col("statut") == "non_recupere").cast("int"))
        .withColumn("cout_evenement_consomme_eur", F.when(F.col("statut") == "consomme", F.col("cout_revient_eur")).otherwise(F.lit(0.0))))
    for col in ["famille", "sous_famille"]:
        menus = menus.withColumn(col, _norm(col))
    for col in ["region", "ville"]:
        sites = sites.withColumn(col, _norm(col))
    diners = diners.withColumn("segment", _norm("segment")).withColumn("age", F.col("age").cast("double"))
    _unique(menus, "id_menu"); _unique(sites, "id_etablissement"); _unique(diners, "id_convive")
    return (meals
        .join(F.broadcast(menus), "id_menu", "left")
        .join(F.broadcast(sites), "id_etablissement", "left")
        .join(F.broadcast(diners.select("id_convive", "segment", "age")), "id_convive", "left"))


def create_spark_session(name: str = "PMD-groupe-03-cantine") -> SparkSession:
    return (SparkSession.builder.appName(name).master("local[*]")
        .config("spark.sql.shuffle.partitions", "16")
        .config("spark.sql.ansi.enabled", "false").getOrCreate())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group-dir", default=str(GROUP_DIR))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")
    try:
        result = build_canteen_dataframe(spark, args.group_dir)
        output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
        result.write.mode("overwrite").partitionBy("annee").parquet(str(output))
        print(f"Parquet output: {output}")
        result.groupBy("region", "famille").agg(
            F.sum("est_consomme").alias("repas_consommes"),
            F.sum("est_annule").alias("annules"),
            F.sum("est_non_recupere").alias("non_recuperes"),
        ).orderBy(F.desc("repas_consommes")).show(30, truncate=False)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
