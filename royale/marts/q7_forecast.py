"""Daily heldout forecasts and actuals; no raw inputs are needed by the page."""
import duckdb
import numpy as np
import pandas as pd

from royale.model import KINDS, TRAIN_START, TRAIN_END, TEST_START, TEST_END, fit

NAME = 'q7_forecast'
QUERY = """
SELECT gaming_date, CAST(coin_in_usd AS DOUBLE) AS coin_in_usd
FROM property_day
WHERE gaming_date BETWEEN DATE '2025-01-01' AND DATE '2025-06-30'
ORDER BY gaming_date
"""


def build(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    daily = con.sql(QUERY).df()
    dates = pd.to_datetime(daily.gaming_date)
    expected = pd.date_range(TRAIN_START, TEST_END)
    if not np.array_equal(dates.to_numpy(), expected.to_numpy()):
        raise ValueError('Expected exactly one property_day row per gaming date Jan–Jun')
    if not np.isfinite(daily.coin_in_usd).all() or (daily.coin_in_usd < 0).any():
        raise ValueError('Actual coin-in must be finite and nonnegative')
    test = daily.loc[dates.between(TEST_START, TEST_END)].copy()
    # Actual holdout outcomes are retained only for scoring and visualization.
    for kind in KINDS:
        model = fit(daily, kind)
        assert model.training_rows == 120 and model.training_end == TRAIN_END
        test[f'{kind}_prediction_usd'] = model.predict(test[['gaming_date']])
    test['training_start'] = TRAIN_START
    test['training_end'] = TRAIN_END
    test['training_days'] = 120
    return test.reset_index(drop=True)
