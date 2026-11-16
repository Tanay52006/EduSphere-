import os
import subprocess
from pathlib import Path

from sqlalchemy import create_engine, inspect

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_make_migrate_uses_the_same_relative_database_as_app() -> None:
    database_name = f"phase2-migrate-{os.getpid()}.db"
    database_path = REPO_ROOT / database_name
    backend_database_path = REPO_ROOT / "backend" / database_name
    for path in (database_path, backend_database_path):
        path.unlink(missing_ok=True)
    try:
        result = subprocess.run(
            ["make", "migrate"],
            cwd=REPO_ROOT,
            env={**os.environ, "DATABASE_URL": f"sqlite:///./{database_name}"},
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert database_path.exists()
        assert not backend_database_path.exists()
        engine = create_engine(f"sqlite:///{database_path}")
        try:
            assert {"users", "documents", "jobs"} <= set(inspect(engine).get_table_names())
        finally:
            engine.dispose()
    finally:
        for path in (database_path, backend_database_path):
            path.unlink(missing_ok=True)
            for suffix in ("-shm", "-wal"):
                path.with_name(path.name + suffix).unlink(missing_ok=True)
