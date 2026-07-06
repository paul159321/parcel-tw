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
SEVEN_ELEVEN_ORDER_ID = os.getenv("SEVEN_ELEVEN_ORDER_ID")
pytestmark = pytest.mark.live

RED = "\033[91m"
DEFAULT = "\033[0m"


def require_order_id() -> str:
    if load_dotenv is None:
        pytest.skip("Install python-dotenv to run live 7-11 tests")
    if SEVEN_ELEVEN_ORDER_ID is None:
        pytest.skip("Set SEVEN_ELEVEN_ORDER_ID to run live 7-11 tests")
    return SEVEN_ELEVEN_ORDER_ID


def test_seven_eleven_valid_order_id():
    result = track(require_order_id(), Platform.SevenEleven)
    assert result is not None
    logging.info(f"{RED}{result.order_id}{DEFAULT} - {result.status}")


def test_seven_eleven_async():
    result = asyncio.run(track_async(require_order_id(), Platform.SevenEleven))
    assert result is not None
    logging.info(f"Async: {RED}{result.order_id}{DEFAULT} - {result.status}")

