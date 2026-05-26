import zipfile
from pathlib import Path

from filecrack.backends import get_backend
from filecrack.core import crack_file, load_wordlist


def test_load_wordlist_skips_empty_lines(tmp_path: Path):
    wordlist = tmp_path / "dict.txt"
    wordlist.write_text("123456\n\nsecret\n", encoding="utf-8")

    assert list(load_wordlist(wordlist)) == ["123456", "secret"]


def test_unencrypted_zip_does_not_match_first_password(tmp_path: Path):
    target = tmp_path / "plain.zip"
    wordlist = tmp_path / "dict.txt"
    wordlist.write_text("wrong\nsecret\n", encoding="utf-8")

    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("hello.txt", "hello")

    result = crack_file(target, wordlist, workers=2)

    assert result.backend == "zip"
    assert result.found is False


def test_office_extensions_use_office_backend(tmp_path: Path):
    target = tmp_path / "demo.docx"
    target.write_bytes(b"not-a-real-docx")

    assert get_backend(target).name == "office"
