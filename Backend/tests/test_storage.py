import pytest

from app.core.ir.models import IRValidationError
from app.core.storage.repository import AnalysisRepository


def test_unsafe_analysis_id_is_rejected(tmp_path):
    repo = AnalysisRepository(data_dir=tmp_path)
    # Path-traversal style ids must not resolve to a file outside data_dir.
    for bad in ["../../etc/passwd", "..\\..\\secret", "a/b", "with space", ""]:
        assert repo.get(bad) is None
        assert repo.exists(bad) is False


def test_safe_uuid_like_id_accepted(tmp_path):
    repo = AnalysisRepository(data_dir=tmp_path)
    # A well-formed id is allowed (returns None only because nothing is stored).
    assert repo.get("d7b5dfde-a18b-4abc-9842-38d1cc665765") is None
    assert repo.exists("d7b5dfde-a18b-4abc-9842-38d1cc665765") is False


def test_corrupt_stored_file_raises_structured_error(tmp_path):
    repo = AnalysisRepository(data_dir=tmp_path)
    (tmp_path / "broken.json").write_text("{ not valid json", encoding="utf-8")
    with pytest.raises(IRValidationError) as exc:
        repo.get("broken")
    assert exc.value.code == "CORRUPT_ANALYSIS"


def test_file_vanishing_after_exists_is_treated_as_missing(tmp_path, monkeypatch):
    # Simulate a delete between the exists() check and read_text(): must return
    # None (missing), not raise CORRUPT_ANALYSIS.
    repo = AnalysisRepository(data_dir=tmp_path)
    target = tmp_path / "ghost.json"
    target.write_text("{}", encoding="utf-8")

    def _raise_fnf(*_args, **_kwargs):
        raise FileNotFoundError("vanished")

    monkeypatch.setattr(type(target), "read_text", _raise_fnf)
    assert repo.get("ghost") is None


def test_list_all_returns_newest_first_and_skips_corrupt(tmp_path):
    from datetime import datetime, timedelta, timezone

    from app.core.ir.models import AnalysisIR, AnalysisResult, Metadata, Node, NodeType

    repo = AnalysisRepository(data_dir=tmp_path)
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for idx, offset in enumerate((0, 2, 1)):  # save order != chronological order
        repo.save(
            AnalysisResult(
                ir=AnalysisIR(
                    analysis_id=f"a{idx}",
                    metadata=Metadata(name=f"A{idx}", uploaded_at=base + timedelta(hours=offset)),
                    nodes=[Node(id="n", type=NodeType.AGENT, name="N")],
                )
            )
        )
    # A corrupt file must be skipped, not abort the whole listing.
    (tmp_path / "broken.json").write_text("{ not valid json", encoding="utf-8")

    listed = repo.list_all()
    assert [r.ir.analysis_id for r in listed] == ["a1", "a2", "a0"]


def test_list_all_empty_when_no_analyses(tmp_path):
    assert AnalysisRepository(data_dir=tmp_path).list_all() == []


def _stored_result(analysis_id: str):
    from app.core.ir.models import AnalysisIR, AnalysisResult, Node, NodeType

    return AnalysisResult(
        ir=AnalysisIR(analysis_id=analysis_id, nodes=[Node(id="n", type=NodeType.AGENT, name="N")])
    )


def test_delete_removes_from_cache_and_disk(tmp_path):
    repo = AnalysisRepository(data_dir=tmp_path)
    repo.save(_stored_result("d1"))
    assert repo.exists("d1")

    assert repo.delete("d1") is True
    # Gone from both layers: no file left and no stale cache hit.
    assert repo.exists("d1") is False
    assert repo.get("d1") is None
    assert list(tmp_path.glob("*.json")) == []


def test_delete_returns_false_when_absent(tmp_path):
    repo = AnalysisRepository(data_dir=tmp_path)
    assert repo.delete("d7b5dfde-a18b-4abc-9842-38d1cc665765") is False


def test_delete_of_uncached_file_still_reports_existed(tmp_path):
    # A fresh repo has an empty cache, so this exercises the disk-only branch.
    AnalysisRepository(data_dir=tmp_path).save(_stored_result("d2"))
    assert AnalysisRepository(data_dir=tmp_path).delete("d2") is True


def test_delete_rejects_unsafe_id(tmp_path):
    repo = AnalysisRepository(data_dir=tmp_path)
    outside = tmp_path.parent / "victim.json"
    outside.write_text("{}", encoding="utf-8")
    for bad in ["../victim", "..\\victim", "a/b", "with space", ""]:
        assert repo.delete(bad) is False
    # The traversal target must be untouched.
    assert outside.exists()


def test_delete_disk_error_raises_structured_error(tmp_path, monkeypatch):
    repo = AnalysisRepository(data_dir=tmp_path)
    repo.save(_stored_result("d3"))

    def _raise_oserror(*_args, **_kwargs):
        raise OSError("permission denied")

    monkeypatch.setattr(type(tmp_path), "unlink", _raise_oserror)
    with pytest.raises(IRValidationError) as exc:
        repo.delete("d3")
    assert exc.value.code == "STORAGE_ERROR"


def test_save_disk_error_raises_structured_error(tmp_path, monkeypatch):
    repo = AnalysisRepository(data_dir=tmp_path)
    from app.core.ir.models import AnalysisIR, AnalysisResult, Node, NodeType

    result = AnalysisResult(ir=AnalysisIR(analysis_id="s1", nodes=[Node(id="n", type=NodeType.AGENT, name="N")]))
    monkeypatch.setattr(type(tmp_path), "write_text", lambda *a, **k: (_ for _ in ()).throw(OSError("disk full")))
    with pytest.raises(IRValidationError) as exc:
        repo.save(result)
    assert exc.value.code == "STORAGE_ERROR"
