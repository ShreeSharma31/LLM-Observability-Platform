import os
import pytest
from sqlalchemy import create_engine, text


@pytest.mark.integration
def test_postgres_connection_env():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run Postgres integration test")

    engine = create_engine(url)
    with engine.connect() as conn:
        value = conn.execute(text("SELECT 1")).scalar()
    assert value == 1
