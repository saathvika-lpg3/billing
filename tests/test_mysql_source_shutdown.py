import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from services.mysql_source import MySqlSource


class SQLiteSourceShutdownTests(unittest.TestCase):
    def test_close_database_resources_closes_registered_connections(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "shutdown_test.db"
            previous = os.environ.get("PRM_SQLITE_DB")
            os.environ["PRM_SQLITE_DB"] = str(db_path)
            try:
                source = MySqlSource()
                conn = sqlite3.connect(source.sqlite_path)
                conn.execute("CREATE TABLE IF NOT EXISTS shutdown_test (id INTEGER)")
                conn.commit()
                source.register_connection(conn)

                source.close_database_resources()

                with self.assertRaises(sqlite3.ProgrammingError):
                    conn.execute("SELECT 1")
            finally:
                if previous is None:
                    os.environ.pop("PRM_SQLITE_DB", None)
                else:
                    os.environ["PRM_SQLITE_DB"] = previous


if __name__ == "__main__":
    unittest.main()
