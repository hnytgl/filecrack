from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class BackendUnavailable(RuntimeError):
    """Raised when an optional backend dependency is missing."""


class UnsupportedFormat(RuntimeError):
    """Raised when no backend supports the file type."""


class CrackBackend(Protocol):
    name: str
    extensions: set[str]

    def verify(self, path: Path, password: str) -> bool:
        ...


@dataclass(frozen=True)
class ZipBackend:
    name: str = "zip"
    extensions: set[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        object.__setattr__(self, "extensions", {".zip", ".jar", ".apk", ".docx", ".xlsx", ".pptx"})

    def verify(self, path: Path, password: str) -> bool:
        if not _zip_has_encrypted_member(path):
            return password == ""
        if _verify_zip_stdlib(path, password):
            return True
        try:
            import pyzipper
        except ImportError:
            return False

        try:
            with pyzipper.AESZipFile(path) as archive:
                names = [name for name in archive.namelist() if not name.endswith("/")]
                if not names:
                    return False
                archive.pwd = password.encode("utf-8")
                with archive.open(names[0]) as handle:
                    handle.read(1)
                return True
        except Exception:
            return False


@dataclass(frozen=True)
class SevenZipBackend:
    name: str = "7z"
    extensions: set[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        object.__setattr__(self, "extensions", {".7z"})

    def verify(self, path: Path, password: str) -> bool:
        try:
            import py7zr
        except ImportError as exc:
            raise BackendUnavailable("7z 支持需要安装 py7zr：pip install filecrack[full]") from exc

        try:
            with py7zr.SevenZipFile(path, mode="r", password=password) as archive:
                archive.test()
            return True
        except Exception:
            return False


@dataclass(frozen=True)
class RarBackend:
    name: str = "rar"
    extensions: set[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        object.__setattr__(self, "extensions", {".rar"})

    def verify(self, path: Path, password: str) -> bool:
        try:
            import rarfile
        except ImportError as exc:
            raise BackendUnavailable("RAR 支持需要安装 rarfile：pip install filecrack[full]") from exc

        try:
            with rarfile.RarFile(path) as archive:
                names = [item.filename for item in archive.infolist() if not item.isdir()]
                if not names:
                    return False
                with archive.open(names[0], pwd=password) as handle:
                    handle.read(1)
                return True
        except Exception:
            return False


@dataclass(frozen=True)
class OfficeBackend:
    name: str = "office"
    extensions: set[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "extensions",
            {".doc", ".xls", ".ppt", ".docx", ".xlsx", ".pptx", ".wps", ".et", ".el", ".dps", ".wpt"},
        )

    def verify(self, path: Path, password: str) -> bool:
        try:
            import msoffcrypto
        except ImportError as exc:
            raise BackendUnavailable("Office/WPS 支持需要安装 msoffcrypto-tool：pip install filecrack[full]") from exc

        try:
            with path.open("rb") as source:
                office = msoffcrypto.OfficeFile(source)
                if not office.is_encrypted():
                    return password == ""
                office.load_key(password=password, verify_password=True)
                output = io.BytesIO()
                office.decrypt(output)
            return True
        except Exception:
            return False


@dataclass(frozen=True)
class PdfBackend:
    name: str = "pdf"
    extensions: set[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        object.__setattr__(self, "extensions", {".pdf"})

    def verify(self, path: Path, password: str) -> bool:
        try:
            import pikepdf
        except ImportError as exc:
            raise BackendUnavailable("PDF 支持需要安装 pikepdf：pip install filecrack[full]") from exc

        try:
            with pikepdf.open(path, password=password):
                return True
        except Exception:
            return False


def get_backend(path: Path, force_format: str | None = None) -> CrackBackend:
    office_extensions = {".doc", ".xls", ".ppt", ".docx", ".xlsx", ".pptx", ".wps", ".et", ".el", ".dps", ".wpt"}
    backends: list[CrackBackend] = [ZipBackend(), SevenZipBackend(), RarBackend(), PdfBackend(), OfficeBackend()]
    suffix = f".{force_format.lower().lstrip('.')}" if force_format else path.suffix.lower()

    if suffix in office_extensions:
        return OfficeBackend()

    for backend in backends:
        if suffix in backend.extensions or force_format == backend.name:
            return backend
    raise UnsupportedFormat(f"暂不支持的文件格式：{suffix or path.name}")


def _verify_zip_stdlib(path: Path, password: str) -> bool:
    try:
        with zipfile.ZipFile(path) as archive:
            names = [name for name in archive.namelist() if not name.endswith("/")]
            if not names:
                return False
            with archive.open(names[0], pwd=password.encode("utf-8")) as handle:
                handle.read(1)
            return True
    except RuntimeError:
        return False
    except (zipfile.BadZipFile, OSError, ValueError):
        return False


def _is_zip_container(path: Path) -> bool:
    try:
        return zipfile.is_zipfile(path)
    except OSError:
        return False


def _zip_has_encrypted_member(path: Path) -> bool:
    try:
        with zipfile.ZipFile(path) as archive:
            return any(info.flag_bits & 0x1 for info in archive.infolist() if not info.is_dir())
    except (zipfile.BadZipFile, OSError):
        return False
