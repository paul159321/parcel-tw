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

EZSHIP_ORDER_ID = os.getenv("EZSHIP_ORDER_ID")
HILIFE_ORDER_ID = os.getenv("HILIFE_ORDER_ID")
pytestmark = pytest.mark.live

RED = "\033[91m"
DEFAULT = "\033[0m"


def require_order_id(env_name: str, value: str | None) -> str:
    if load_dotenv is None:
        pytest.skip("Install python-dotenv to run live ezShip tests")
    if value is None:
        pytest.skip(f"Set {env_name} to run this live test")
    return value


def test_ezship_live():
    result = track(require_order_id("EZSHIP_ORDER_ID", EZSHIP_ORDER_ID), Platform.EzShip)
    assert result is not None
    logging.info(f"{RED}{result.order_id}{DEFAULT} - {result.status}")


def test_ezship_live_async():
    order_id = require_order_id("EZSHIP_ORDER_ID", EZSHIP_ORDER_ID)
    result = asyncio.run(track_async(order_id, Platform.EzShip))
    assert result is not None
    logging.info(f"Async: {RED}{result.order_id}{DEFAULT} - {result.status}")


def test_hilife_live():
    result = track(require_order_id("HILIFE_ORDER_ID", HILIFE_ORDER_ID), Platform.HiLife)
    assert result is not None
    logging.info(f"{RED}{result.order_id}{DEFAULT} - {result.status}")


def test_hilife_live_async():
    order_id = require_order_id("HILIFE_ORDER_ID", HILIFE_ORDER_ID)
    result = asyncio.run(track_async(order_id, Platform.HiLife))
    assert result is not None
    logging.info(f"Async: {RED}{result.order_id}{DEFAULT} - {result.status}")
