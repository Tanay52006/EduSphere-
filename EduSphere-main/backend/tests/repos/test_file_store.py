import pytest

from app.repos.file_store import LocalFileStore, PathTraversalError


def test_file_store_rejects_path_traversal(tmp_path):
    store = LocalFileStore(tmp_path)

    with pytest.raises(PathTraversalError):
        store.save("../outside.txt", b"secret")


def test_file_store_uses_random_storage_names(tmp_path):
    store = LocalFileStore(tmp_path)

    path = store.save("notes.txt", b"hello")

    assert path.parent == tmp_path.resolve()
    assert path.name != "notes.txt"
    assert path.read_bytes() == b"hello"
