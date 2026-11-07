"""Synthetic retail data for a dry run of /eda and /baseline.

    uv run python scripts/make_sample_data.py

Writes data/raw/_sample/{sales,products,stores}.csv with 5 planted data bugs.
The answer key is at the bottom of SETUP.md. Check it after the dry run to see
whether /eda and /baseline caught them.

Delete data/raw/_sample before the real data arrives.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.paths import RAW  # noqa: E402

rng = np.random.default_rng(7)
out = RAW / "_sample"
out.mkdir(parents=True, exist_ok=True)

stores = pd.DataFrame({
    "store_id": range(1, 9),
    "region": rng.choice(["North", "South", "East", "West"], 8),
    "size_sqft": rng.integers(8_000, 40_000, 8),
})

cats = ["produce", "dairy", "snacks", "beverages", "frozen"]
products = pd.DataFrame({
    "product_id": range(1, 41),
    "category": rng.choice(cats, 40),
    "base_price": rng.uniform(1.5, 12, 40).round(2),
})
dup = products[products.product_id == 17].assign(category="snacks")
products = pd.concat([products, dup], ignore_index=True)

dates = pd.date_range("2025-01-01", "2025-12-31", freq="D")
grid = pd.MultiIndex.from_product([dates, range(1, 10), range(1, 41)],
                                  names=["date", "store_id", "product_id"]).to_frame(index=False)
grid = grid[~((grid.store_id == 9) & (rng.random(len(grid)) > 0.15))]
grid = grid[~((grid.store_id == 3) & (grid.date >= "2025-03-04") & (grid.date <= "2025-03-27"))]

base = products.drop_duplicates("product_id").set_index("product_id")["base_price"]
dow = grid.date.dt.day_of_week
season = 1 + 0.25 * np.sin(2 * np.pi * grid.date.dt.day_of_year / 365)
promo = rng.random(len(grid)) < 0.08
price = (grid.product_id.map(base) * np.where(promo, 0.8, 1.0)).round(2).to_numpy(copy=True)
lam = 6 * season * np.where(dow >= 5, 1.4, 1.0) * np.where(promo, 1.8, 1.0) * (grid.store_id % 4 + 1) / 2.5
units = rng.poisson(lam).astype(int)
units[rng.random(len(units)) < 0.004] *= -1
price[rng.random(len(price)) < 0.002] = -1.0

sales = grid.assign(units=units, price=price, promo=promo.astype(int))
sales["revenue"] = (sales.units * sales.price).round(2)
sales["date"] = sales.date.dt.strftime("%Y-%m-%d")

stores.to_csv(out / "stores.csv", index=False)
products.to_csv(out / "products.csv", index=False)
sales.to_csv(out / "sales.csv", index=False)
print(f"wrote {len(sales):,} sales rows, {len(products)} product rows, {len(stores)} stores to {out}")
print("dry run: /eda data/raw/_sample   then   /baseline units sales")
