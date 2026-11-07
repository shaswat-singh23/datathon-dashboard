"""Clean the sales panel. Fixes from EDA.md "Data quality issues".

    uv run python -m src.clean            # writes data/processed/sales_clean.parquet

    from src.clean import clean_sales
    df = clean_sales()                    # polars DataFrame, one row per date x store x product

Fixes:
1. products: dedupe on product_id (id 17 was duplicated -> join fan-out).
2. price == -1 sentinel: rebuilt as base_price * (0.8 if promo else 1), which matches every valid row exactly.
3. units < 0: set to null (sign flip suspected but unconfirmed); rows stay so calendar lags line up.
4. store 9 missing from stores.csv: left join, region "unknown", size_sqft null.
5. store 3 gap 2025-03-04..03-27: rows are absent; left absent (lags computed on the calendar, not row order).
6. revenue: recomputed from cleaned units * price; never a feature for units.
"""

from __future__ import annotations

import polars as pl

from src import io
from src.paths import RAW

SAMPLE = RAW / "_sample"


def clean_sales(folder=SAMPLE, verbose: bool = True) -> pl.DataFrame:
    log = print if verbose else (lambda *a, **k: None)
    sales = io.load(folder / "sales.csv")
    products = io.load(folder / "products.csv")
    stores = io.load(folder / "stores.csv")

    # 1. dedupe products
    n0 = products.height
    products = products.unique("product_id", keep="first").sort("product_id")
    log(f"products: {n0} -> {products.height} rows after dedupe on product_id")
    assert products["product_id"].is_unique().all()
    assert stores["store_id"].is_unique().all()

    # many:1 join to products (expect 1:1 match per sales row)
    n = sales.height
    df = sales.join(products, on="product_id", how="left", validate="m:1")
    log(f"sales x products (m:1, left): {n:,} -> {df.height:,} rows; "
        f"unmatched {df['base_price'].null_count()}")
    assert df.height == n

    # 4. many:1 join to stores, keep store 9
    df = df.join(stores, on="store_id", how="left", validate="m:1")
    log(f"sales x stores (m:1, left): {n:,} -> {df.height:,} rows; "
        f"unmatched rows {df['region'].null_count():,} "
        f"(store_ids {sorted(df.filter(pl.col('region').is_null())['store_id'].unique().to_list())})")
    assert df.height == n
    df = df.with_columns(pl.col("region").fill_null("unknown"))

    # 2. price sentinel
    rebuilt = (pl.col("base_price") * pl.when(pl.col("promo") == 1).then(0.8).otherwise(1.0)).round(2)
    n_sent = df.filter(pl.col("price") < 0).height
    n_valid_mismatch = df.filter((pl.col("price") >= 0) & ((pl.col("price") - rebuilt).abs() > 0.011)).height
    df = df.with_columns(pl.when(pl.col("price") < 0).then(rebuilt).otherwise(pl.col("price")).alias("price"))
    log(f"price: rebuilt {n_sent} sentinel (-1) rows; rule mismatches on valid rows: {n_valid_mismatch}")

    # 3. negative units -> null
    n_neg = df.filter(pl.col("units") < 0).height
    df = df.with_columns(pl.when(pl.col("units") < 0).then(None).otherwise(pl.col("units")).alias("units"))
    log(f"units: {n_neg} negative values set to null")

    # 6. revenue recomputed
    df = df.with_columns((pl.col("units") * pl.col("price")).round(2).alias("revenue"))
    return df.sort("store_id", "product_id", "date")


if __name__ == "__main__":
    out = io.save(clean_sales(), "sales_clean")
    print(f"wrote {out}")
