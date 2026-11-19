import hashlib

from core.hasher import calculate_sha256


def test_calculate_sha256(tmp_path):
    sample = tmp_path / "sample.txt"
    sample.write_bytes(b"file integrity monitoring")
    assert calculate_sha256(sample) == hashlib.sha256(
        b"file integrity monitoring"
    ).hexdigest()
