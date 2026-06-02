import os


def test_always_passes():
    assert True


def test_project_structure():
    assert os.path.isdir("/app")
    assert os.path.exists("/app/Makefile")
