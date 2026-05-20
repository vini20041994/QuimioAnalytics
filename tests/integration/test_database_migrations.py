from pathlib import Path
import re

import pytest


@pytest.mark.integration
def test_migration_files_follow_expected_pattern_and_are_not_empty():
    migrations_dir = Path(__file__).resolve().parents[2] / "database" / "migrations"
    files = sorted(migrations_dir.glob("*.sql"))

    assert files, "Nenhum arquivo de migration encontrado em database/migrations"

    pattern = re.compile(r"^\d{3}_.+\.sql$")
    for migration_file in files:
        assert pattern.match(migration_file.name), f"Nome inválido de migration: {migration_file.name}"
        content = migration_file.read_text(encoding="utf-8").strip()
        assert content, f"Migration vazia: {migration_file.name}"


@pytest.mark.integration
def test_migration_files_are_uniquely_numbered():
    migrations_dir = Path(__file__).resolve().parents[2] / "database" / "migrations"
    files = sorted(migrations_dir.glob("*.sql"))

    prefixes = [f.name.split("_", 1)[0] for f in files if "_" in f.name]
    assert len(prefixes) == len(set(prefixes)), "Existem migrations com prefixos numéricos duplicados"
