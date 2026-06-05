import json
import ssl
from typing import Any

import httpx

from .base import Tracker, TrackingInfo, RequestHandler, TrackingInfoAdapter, NetworkError
from .enums import Platform

SEARCH_URL = "https://ecfme.fme.com.tw/FMEDCFPWebV2_II/list.aspx/GetOrderDetail"


def get_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.set_ciphers("DEFAULT@SECLEVEL=1")
    ctx.options |= 0x4
    return ctx


class FamilyMartTracker(Tracker):
    def __init__(self):
        self.tracking_info = None

    def track_status(self, order_id: str) -> TrackingInfo | None:
        data = FamilyMartRequestHandler().get_data(order_id)
        self.tracking_info = FamilyMartTrackingInfoAdapter.convert(data)
        return self.tracking_info

    async def track_status_async(self, order_id: str) -> TrackingInfo | None:
        data = await FamilyMartRequestHandler().get_data_async(order_id)
        self.tracking_info = FamilyMartTrackingInfoAdapter.convert(data)
        return self.tracking_info


class FamilyMartRequestHandler(RequestHandler):
    def get_data(self, order_id: str) -> dict:
        headers = {"Content-Type": "application/json; charset=UTF-8"}
        payload = {"EC_ORDER_NO": order_id, "ORDER_NO": order_id, "RCV_USER_NAME": None}

        try:
            with httpx.Client(verify=get_ssl_context(), timeout=15) as client:
                response = client.post(SEARCH_URL, json=payload, headers=headers)
                response.raise_for_status()
                result = self._parse_response(response.text)
                return result
        except Exception as e:
            raise NetworkError(f"FamilyMart request failed: {e}")

    async def get_data_async(self, order_id: str) -> dict:
        headers = {"Content-Type": "application/json; charset=UTF-8"}
        payload = {"EC_ORDER_NO": order_id, "ORDER_NO": order_id, "RCV_USER_NAME": None}

        try:
            async with httpx.AsyncClient(verify=get_ssl_context(), timeout=15) as client:
                response = await client.post(SEARCH_URL, json=payload, headers=headers)
                response.raise_for_status()
                result = self._parse_response(response.text)
                return result
        except Exception as e:
            raise NetworkError(f"FamilyMart async request failed: {e}")

    def _parse_response(self, response_text: str) -> dict:
        s = response_text.replace("\\", "")
        json_data = json.loads(s[6:-2])
        return json_data


class FamilyMartTrackingInfoAdapter(TrackingInfoAdapter):
    @staticmethod
    def convert(raw_data: Any, order_id: str | None = None) -> TrackingInfo | None:
        if not raw_data or "List" not in raw_data or len(raw_data["List"]) == 0:
            return None

        status_list = raw_data["List"]
        latest_status = status_list[0]

        oid = latest_status["ORDER_NO"]
        time_str = latest_status["ORDER_DATE_R"] + ":00"
        status_message = latest_status["STATUS_D"]
        is_delivered = (
            "貨件配達取件店舖" in status_message or "已完成取件" in status_message
        )
        return TrackingInfo(
            order_id=oid,
            platform=Platform.FamilyMart.value,
            status=status_message,
            time=time_str,
            is_delivered=is_delivered,
            raw_data=raw_data,
        )
