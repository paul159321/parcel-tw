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

    result = track(Platform.OKMart, OKMART_ORDER_ID)
    assert result is not None
    logging.info(f"{RED}{result.order_id}{DEFAULT} - {result.status}")


def test_okmart_invalid_order_id():
    result = track(Platform.OKMart, "123456789")
    assert result is None
