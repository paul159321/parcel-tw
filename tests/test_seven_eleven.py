import logging
import os

from dotenv import load_dotenv

from parcel_tw import Platform, track

load_dotenv()
SEVEN_ELEVEN_ORDER_ID = os.getenv("SEVEN_ELEVEN_ORDER_ID")

RED = "\033[91m"
DEFAULT = "\033[0m"


def test_seven_eleven_valid_order_id():
    assert SEVEN_ELEVEN_ORDER_ID is not None

    result = track(Platform.SevenEleven, SEVEN_ELEVEN_ORDER_ID)
    assert result is not None
    logging.info(f"{RED}{result.order_id}{DEFAULT} - {result.status}")


def test_seveneleven_invalid_order_id():
    result = track(Platform.SevenEleven, "1234567890")
    assert result is None
