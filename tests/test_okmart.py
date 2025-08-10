import logging
import os

from dotenv import load_dotenv

from parcel_tw import Platform, track

load_dotenv()
OKMART_ORDER_ID = os.getenv("OKMART_ORDER_ID")

RED = "\033[91m"
DEFAULT = "\033[0m"


def test_okmart():
    assert OKMART_ORDER_ID is not None

    result = track(OKMART_ORDER_ID, Platform.OKMart)
    assert result is not None
    logging.info(f"{RED}{result.order_id}{DEFAULT} - {result.status}")


def test_okmart_invalid_order_id():
    result = track("123456789", Platform.OKMart)
    assert result is None
