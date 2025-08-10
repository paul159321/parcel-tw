import logging
import os

from dotenv import load_dotenv

from parcel_tw import Platform, track

load_dotenv()
FAMILY_MART_ORDER_ID = os.getenv("FAMILY_MART_ORDER_ID")

RED = "\033[91m"
DEFAULT = "\033[0m"

def test_family_mart():
    assert FAMILY_MART_ORDER_ID is not None

    result = track(FAMILY_MART_ORDER_ID, Platform.FamilyMart)
    assert result is not None
    logging.info(f"{RED}{result.order_id}{DEFAULT} - {result.status}")

def test_family_mart_invalid_order_id():
    result = track("1234567890", Platform.FamilyMart)
    assert result is None