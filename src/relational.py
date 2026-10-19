"""Safe relational operations used by the aggregation and star-schema lesson."""

import pandas as pd


def safe_merge(left, right, **kwargs):
    """Merge two frames, guarding left-join row counts and reporting unmatched rows.

    The unmatched rate is measured on rows from ``left``. A left join must
    preserve the row count; ``validate`` can additionally enforce key cardinality.
    """
    how = kwargs.get("how", "inner")
    if how == "left" and "indicator" in kwargs:
        raise ValueError("safe_merge réserve le paramètre indicator pour son contrôle")

    before = len(left)
    merge_kwargs = dict(kwargs)
    merge_kwargs["indicator"] = "_safe_merge_status"
    merged = left.merge(right, **merge_kwargs)

    unmatched = int(merged["_safe_merge_status"].eq("left_only").sum())
    unmatched_rate = unmatched / before if before else 0.0
    print(
        f"safe_merge : {unmatched} ligne(s) non appariée(s) sur {before} "
        f"({unmatched_rate:.2%} des lignes de gauche)"
    )
    merged = merged.drop(columns="_safe_merge_status")

    if how == "left" and len(merged) != before:
        raise ValueError(
            f"La jointure left a changé le nombre de lignes : {before} -> {len(merged)}. "
            "Vérifiez la cardinalité des clés à droite."
        )
    return merged


def check_referential_integrity(fact_table, dimensions):
    """Print orphan counts for FK columns and raise if any orphan is found.

    ``dimensions`` maps a fact foreign-key column name to a dimension DataFrame
    containing a primary-key column with the same name.
    """
    orphan_counts = {}
    for key, dimension in dimensions.items():
        if key not in fact_table.columns:
            raise KeyError(f"Clé étrangère absente de la table de faits : {key}")
        if key not in dimension.columns:
            raise KeyError(f"Clé primaire {key} absente de sa dimension")

        fact_keys = fact_table[key]
        orphan_mask = fact_keys.notna() & ~fact_keys.isin(dimension[key])
        orphan_count = int(orphan_mask.sum())
        orphan_counts[key] = orphan_count
        print(f"{key} : {orphan_count} clé(s) orpheline(s)")

    total_orphans = sum(orphan_counts.values())
    if total_orphans:
        details = ", ".join(
            f"{key}={count}" for key, count in orphan_counts.items() if count
        )
        raise ValueError(f"Intégrité référentielle violée : {details}")
    return orphan_counts
