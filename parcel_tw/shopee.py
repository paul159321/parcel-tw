import logging
import time
from hashlib import sha256
from typing import Final, Any

import httpx

from .base import Tracker, TrackingInfo, RequestHandler, TrackingInfoAdapter, NetworkError
from .enums import Platform

SEARCH_URL: Final = "https://spx.tw/api/v2/fleet_order/tracking/search"
SALT: Final = b"MGViZmZmZTYzZDJhNDgxY2Y1N2ZlN2Q1ZWJkYzlmZDY="  # Shopee API hashing salt


class ShopeeTracker(Tracker):
    def __init__(self):
        self.tracking_info = None

    def track_status(self, order_id: str) -> TrackingInfo | None:
        data = ShopeeRequestHandler().get_data(order_id)
        self.tracking_info = ShopeeTrackingInfoAdapter.convert(data)
        return self.tracking_info

    async def track_status_async(self, order_id: str) -> TrackingInfo | None:
        data = await ShopeeRequestHandler().get_data_async(order_id)
        self.tracking_info = ShopeeTrackingInfoAdapter.convert(data)
        return self.tracking_info


class ShopeeRequestHandler(RequestHandler):
    def get_data(self, order_id: str) -> dict:
        timestamp = int(time.time())
        headers = {
            "cookie": "fms_language=tw",
        }
        params = {
            "sls_tracking_number": order_id
            + "|"
            + str(timestamp)
            + sha256(order_id.encode() + str(timestamp).encode() + SALT).hexdigest()
        }
        try:
            with httpx.Client(timeout=15) as client:
                response = client.get(SEARCH_URL, params=params, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise NetworkError(f"Shopee request failed: {e}")

    async def get_data_async(self, order_id: str) -> dict:
        timestamp = int(time.time())
        headers = {
            "cookie": "fms_language=tw",
        }
        params = {
            "sls_tracking_number": order_id
            + "|"
            + str(timestamp)
            + sha256(order_id.encode() + str(timestamp).encode() + SALT).hexdigest()
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(SEARCH_URL, params=params, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise NetworkError(f"Shopee async request failed: {e}")


class ShopeeTrackingInfoAdapter(TrackingInfoAdapter):
    @staticmethod
    def convert(raw_data: Any, order_id: str | None = None) -> TrackingInfo | None:
        if not raw_data or "data" not in raw_data:
            return None
        data = raw_data["data"]
        if data is None or len(data) == 0:
            return None

        oid = data.get("sls_tracking_number")
        tracking_list = data.get("tracking_list")
        if not tracking_list:
            return None

        latest_status = tracking_list[0]
        latest_status_message = latest_status.get("message")

        timestamp = latest_status.get("timestamp")
        datetime_val = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

        status = latest_status.get("status")
        is_delivered = (
            "SP_Ready_Collection" in status or "SP_Collection_Collected" in status
        )

        return TrackingInfo(
            order_id=oid,
            platform=Platform.Shopee.value,
            status=latest_status_message,
            time=datetime_val,
            is_delivered=is_delivered,
            raw_data=data,
        )
