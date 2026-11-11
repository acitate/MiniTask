import pytest

from minitask.database import Database


@pytest.fixture
def database(tmp_path):
    db = Database(tmp_path / "minitask.sqlite3")
    try:
        yield db
    finally:
        db.close()
