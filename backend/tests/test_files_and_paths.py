from pathlib import Path

import pytest

from app.core.constants import ContentType
from app.core.exceptions import InvalidFileError, PublishError
from app.utils.files import validate_upload_name
from app.utils.paths import build_view_url, safe_child
from app.utils.slug import safe_slug


@pytest.mark.parametrize("name", ["../secret.pdf", "..\\secret.pdf", "/tmp/secret.pdf", "C:\\secret.pdf"])
def test_rejects_path_traversal_names(name: str) -> None:
    with pytest.raises(InvalidFileError):
        validate_upload_name(name, ContentType.PDF)


def test_extension_validation() -> None:
    assert validate_upload_name("deck.PPTX", ContentType.PPT) == "deck.PPTX"
    with pytest.raises(InvalidFileError):
        validate_upload_name("deck.exe", ContentType.PPT)


def test_safe_child_and_url(tmp_path: Path) -> None:
    assert safe_child(tmp_path, "content", "index.html").is_relative_to(tmp_path.resolve())
    with pytest.raises(PublishError):
        safe_child(tmp_path, "..", "outside")
    assert build_view_url("https://internal.example/base/", "/12-demo/") == "https://internal.example/base/12-demo/"
    assert safe_slug("Quarterly Report 2026") == "quarterly-report-2026"
