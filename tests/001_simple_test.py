import os


def test_always_passes():
    assert True


def test_project_structure():
    assert os.path.isdir("/app")  # проверим, что папка смонтирована
    assert os.path.exists("/app/Makefile")  # например
