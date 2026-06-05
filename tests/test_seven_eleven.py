import asyncio
import logging
import os

from dotenv import load_dotenv

from parcel_tw import Platform, track, track_async

load_dotenv()
SEVEN_ELEVEN_ORDER_ID = os.getenv("SEVEN_ELEVEN_ORDER_ID")

RED = "\033[91m"
DEFAULT = "\033[0m"


def test_seven_eleven_valid_order_id():
    assert SEVEN_ELEVEN_ORDER_ID is not None

    result = track(SEVEN_ELEVEN_ORDER_ID, Platform.SevenEleven)
    assert result is not None
    logging.info(f"{RED}{result.order_id}{DEFAULT} - {result.status}")


def test_seven_eleven_async():
    assert SEVEN_ELEVEN_ORDER_ID is not None

    result = asyncio.run(track_async(SEVEN_ELEVEN_ORDER_ID, Platform.SevenEleven))
    assert result is not None
    logging.info(f"Async: {RED}{result.order_id}{DEFAULT} - {result.status}")


def test_seveneleven_invalid_order_id():
    result = track("1234567890", Platform.SevenEleven)
    assert result is None

