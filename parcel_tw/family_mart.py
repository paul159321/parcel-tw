import json
import logging
import ssl

import requests
from requests.adapters import HTTPAdapter

from .base import Tracker, TrackingInfo, RequestHandler, TrackingInfoAdapter
from .enums import Platform

SEARCH_URL = "https://ecfme.fme.com.tw/FMEDCFPWebV2_II/list.aspx/GetOrderDetail"


# stackoveflow solution for requests.exceptions.SSLError
# https://stackoverflow.com/questions/77303136
class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        ctx.options |= 0x4
        kwargs["ssl_context"] = ctx
        return super(TLSAdapter, self).init_poolmanager(*args, **kwargs)


class FamilyMartTracker(Tracker):
    def __init__(self):
        self.tracking_info = None

    def track_status(self, order_id: str) -> TrackingInfo | None:
        try:
            data = FamilyMartRequestHandler().get_data(order_id)
        except Exception as e:
            logging.error(f"[FamilyMart] {e}")
            return None

        self.tracking_info = FamilyMartTrackingInfoAdapter.convert(data)

        return self.tracking_info


class FamilyMartRequestHandler(RequestHandler):
    def __init__(self):
        super().__init__()
        self.session.mount("https://", TLSAdapter())  # used to avoid SSLError

    def get_data(self, order_id: str) -> dict:
        #logging.info("[FamilyMart] Sending post request to the search page...")

        headers = {"Content-Type": "application/json; charset=UTF-8"}
        payload = {"EC_ORDER_NO": order_id, "ORDER_NO": order_id, "RCV_USER_NAME": None}

        response = self.session.post(SEARCH_URL, json=payload, headers=headers)

        result = self._parse_response(response.text)
        return result

    def _parse_response(self, response):
        #logging.info("[FamilyMart] Parsing the response...")
        s = response.replace("\\", "")
        json_data = json.loads(s[6:-2])

        return json_data


class FamilyMartTrackingInfoAdapter(TrackingInfoAdapter):
    @staticmethod
    def convert(raw_data: dict) -> TrackingInfo | None:
        if len(raw_data["List"]) == 0:
            return None

        status_list = raw_data["List"]
        latest_status = status_list[0]  # First element in the list is the latest status

        order_id = latest_status["ORDER_NO"]
        time = latest_status["ORDER_DATE_R"] + ":00"  # Add seconds to the time
        status_message = latest_status["STATUS_D"]
        is_delivered = (
            "貨件配達取件店舖" in status_message or "已完成取件" in status_message
        )
        return TrackingInfo(
            order_id=order_id,
            platform=Platform.FamilyMart.value,
            status=status_message,
            time=time,
            is_delivered=is_delivered,
            raw_data=raw_data,
        )
