import asyncio
import logging
import os

from dotenv import load_dotenv

from parcel_tw import Platform, track, track_async

load_dotenv()
SHOPEE_ORDER_ID = os.getenv("SHOPEE_ORDER_ID")

RED = "\033[91m"
DEFAULT = "\033[0m"


def test_shopee_valid_order_id():
    assert SHOPEE_ORDER_ID is not None

    result = track(SHOPEE_ORDER_ID, Platform.Shopee)
    assert result is not None
    logging.info(f"{RED}{result.order_id}{DEFAULT} - {result.status}")


def test_shopee_async():
    assert SHOPEE_ORDER_ID is not None

    result = asyncio.run(track_async(SHOPEE_ORDER_ID, Platform.Shopee))
    assert result is not None
    logging.info(f"Async: {RED}{result.order_id}{DEFAULT} - {result.status}")


def test_shopee_invalid_order_id():
    result = track("1234567890", Platform.Shopee)
    assert result is None


