import asyncio
import logging
import os

import pytest

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None

from parcel_tw import Platform, track, track_async

if load_dotenv is not None:
    load_dotenv()
FAMILY_MART_ORDER_ID = os.getenv("FAMILY_MART_ORDER_ID")
pytestmark = pytest.mark.live

RED = "\033[91m"
DEFAULT = "\033[0m"


def require_order_id() -> str:
    if load_dotenv is None:
        pytest.skip("Install python-dotenv to run live FamilyMart tests")
    if FAMILY_MART_ORDER_ID is None:
        pytest.skip("Set FAMILY_MART_ORDER_ID to run live FamilyMart tests")
    return FAMILY_MART_ORDER_ID


def test_family_mart():
    result = track(require_order_id(), Platform.FamilyMart)
    assert result is not None
    logging.info(f"{RED}{result.order_id}{DEFAULT} - {result.status}")


def test_family_mart_async():
    result = asyncio.run(track_async(require_order_id(), Platform.FamilyMart))
    assert result is not None
    logging.info(f"Async: {RED}{result.order_id}{DEFAULT} - {result.status}")
