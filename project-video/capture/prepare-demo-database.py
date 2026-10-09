"""Create and migrate one new local demo database; refuse an existing name."""
from pathlib import Path
import json
import os
import subprocess
import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT.parent.parent / "draftly-platform" / "backend"
NAME = "draftly_video_workflow_v2"
URL = f"postgresql+psycopg://film@127.0.0.1:5439/{NAME}"

with psycopg.connect("host=127.0.0.1 port=5439 user=film dbname=postgres", autocommit=True) as connection:
    exists = connection.execute("SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname=%s)", (NAME,)).fetchone()[0]
    if exists:
        raise SystemExit("Refusing to reset or migrate an existing database with the requested demo name.")
    connection.execute(sql.SQL("CREATE DATABASE {} OWNER film").format(sql.Identifier(NAME)))
    print("Created new local database: " + NAME)
env = os.environ.copy()
env.update({"DATABASE_URL": URL, "DATABASE_URL_DIRECT": URL, "ENVIRONMENT": "test", "GEMINI_API_KEY": ""})
subprocess.run([str(BACKEND / ".venv" / "Scripts" / "python.exe"), "-m", "alembic", "upgrade", "head"],
               cwd=BACKEND, env=env, check=True)
(ROOT / "out" / "demo-database.json").write_text(json.dumps({"name": NAME, "host": "127.0.0.1", "port": 5439,
    "created_new": True, "migrations": "head"}, indent=2), encoding="utf-8")
print("New local database migrated to head.")
