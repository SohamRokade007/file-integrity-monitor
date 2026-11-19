import pytest

from core.integrity import check_integrity, create_baseline
from database.db_manager import DatabaseManager


def test_detects_added_modified_and_deleted_files(tmp_path):
    monitored = tmp_path / "monitored"
    monitored.mkdir()
    database = DatabaseManager(tmp_path / "db" / "test.db")

    (monitored / "same.txt").write_text("original", encoding="utf-8")
    (monitored / "delete.txt").write_text("remove me", encoding="utf-8")
    create_baseline(monitored, database)

    (monitored / "same.txt").write_text("changed content", encoding="utf-8")
    (monitored / "delete.txt").unlink()
    (monitored / "new.txt").write_text("new file", encoding="utf-8")

    result = check_integrity(monitored, database)
    assert [item["path"] for item in result["added"]] == ["new.txt"]
    assert [item["path"] for item in result["modified"]] == ["same.txt"]
    assert [item["path"] for item in result["deleted"]] == ["delete.txt"]


def test_rejects_checking_a_different_directory(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    database = DatabaseManager(tmp_path / "db" / "test.db")
    create_baseline(first, database)

    with pytest.raises(ValueError, match="differs from the baseline"):
        check_integrity(second, database)
