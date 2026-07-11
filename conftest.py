from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config) -> None:
    """Use a unique repo-local temp root unless the caller chose one."""
    if config.option.basetemp is None:
        config.option.basetemp = str(
            ROOT / "tmp" / f"pytest-{os.getpid()}-{uuid.uuid4().hex}"
        )
