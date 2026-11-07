import pytest

from royale import config, io

needs_data = pytest.mark.skipif(not config.data_available(), reason="DATA_DIR has no data")


def test_registry_paths_are_parquet():
    assert all(rel.endswith(".parquet") for rel in config.TABLES.values())


@needs_data
def test_property_day_has_181_gaming_days():
    assert len(io.table("property_day")) == 181


@needs_data
def test_sql_views_work():
    n = io.sql("SELECT count(*) AS n FROM calendar_day")["n"].iloc[0]
    assert n == 181
