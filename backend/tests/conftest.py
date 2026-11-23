from pathlib import Path

import pytest

from .content_fixtures import make_foundation, make_s1_content


@pytest.fixture
def foundation(tmp_path: Path) -> Path:
    return make_foundation(tmp_path)


@pytest.fixture
def s1(foundation: Path) -> Path:
    return make_s1_content(foundation)
