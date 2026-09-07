from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.db.base import Base
from app.db import models  # noqa: F401


def test_metadata_contains_exactly_seven_postgresql_tables() -> None:
    assert set(Base.metadata.tables) == {
        "users", "categories", "contents", "publish_targets", "review_records", "publish_records", "operation_logs",
    }


def test_postgresql_specific_types_and_constraints_compile() -> None:
    dialect = postgresql.dialect()
    targets_sql = str(CreateTable(Base.metadata.tables["publish_targets"]).compile(dialect=dialect))
    contents_sql = str(CreateTable(Base.metadata.tables["contents"]).compile(dialect=dialect))
    assert "JSONB" in targets_sql
    assert "TIMESTAMP WITH TIME ZONE" in targets_sql
    assert "ck_contents_content_type_allowed" in contents_sql
    assert "ON DELETE RESTRICT" in contents_sql
