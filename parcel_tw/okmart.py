import logging
import re
from typing import Final, Any

import httpx
from bs4 import BeautifulSoup

from .base import Tracker, TrackingInfo, RequestHandler, TrackingInfoAdapter, NetworkError, CaptchaError
from .enums import Platform

VALIDATE_URL: Final = "https://ecservice.okmart.com.tw/Tracking/ValidateNumber.ashx"
RESULT_URL: Final = "https://ecservice.okmart.com.tw/Tracking/Result"


class OKMartTracker(Tracker):
    def __init__(self) -> None:
        self.tracking_info = None

    def track_status(self, order_id: str) -> TrackingInfo | None:
        order_id = self.normalize_order_id(order_id)
        if order_id is None:
            return None
        data = OKMartRequestHandler().get_data(order_id)
        self.tracking_info = OKMartTrackingInfoAdapter.convert(data)
        return self.tracking_info

    async def track_status_async(self, order_id: str) -> TrackingInfo | None:
        order_id = self.normalize_order_id(order_id)
        if order_id is None:
            return None
        data = await OKMartRequestHandler().get_data_async(order_id)
        self.tracking_info = OKMartTrackingInfoAdapter.convert(data)
        return self.tracking_info


class OKMartRequestHandler(RequestHandler):
    def get_data(self, order_id: str) -> dict:
        with httpx.Client(timeout=15) as client:
            validate_code = self._get_validate_code(client)
            if validate_code is None:
                raise CaptchaError("Failed to get validate code")

            response = self._get_search_result(client, order_id, validate_code)
            result = OKMartResponseParser(response.text).parse()
            return result

    async def get_data_async(self, order_id: str) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            validate_code = await self._get_validate_code_async(client)
            if validate_code is None:
                raise CaptchaError("Failed to get validate code")

            response = await self._get_search_result_async(client, order_id, validate_code)
            result = OKMartResponseParser(response.text).parse()
            return result

    def _get_validate_code(self, client: httpx.Client) -> str | None:
        try:
            response = client.get(VALIDATE_URL)
            cookie = response.headers.get("Set-Cookie", "")
            matchobj = re.search(r"ValidateNumber=code=(.....); path=/", cookie)
            if matchobj:
                return matchobj.group(1)
        except Exception as e:
            raise NetworkError(f"Failed to get OKMart validate code: {e}")
        return None

    async def _get_validate_code_async(self, client: httpx.AsyncClient) -> str | None:
        try:
            response = await client.get(VALIDATE_URL)
            cookie = response.headers.get("Set-Cookie", "")
            matchobj = re.search(r"ValidateNumber=code=(.....); path=/", cookie)
            if matchobj:
                return matchobj.group(1)
        except Exception as e:
            raise NetworkError(f"Failed to get OKMart validate code: {e}")
        return None

    def _get_search_result(
        self, client: httpx.Client, order_id: str, validate_code: str
    ) -> httpx.Response:
        headers = {
            "Cookie": f"ValidateNumber=code={validate_code}&odno={order_id}&cutknm=&cutktl="
        }
        params = {"inputOdNo": order_id, "inputCode1": validate_code}
        try:
            response = client.get(RESULT_URL, params=params, headers=headers)
            response.raise_for_status()
            return response
        except Exception as e:
            raise NetworkError(f"Failed to get OKMart search result: {e}")

    async def _get_search_result_async(
        self, client: httpx.AsyncClient, order_id: str, validate_code: str
    ) -> httpx.Response:
        headers = {
            "Cookie": f"ValidateNumber=code={validate_code}&odno={order_id}&cutknm=&cutktl="
        }
        params = {"inputOdNo": order_id, "inputCode1": validate_code}
        try:
            response = await client.get(RESULT_URL, params=params, headers=headers)
            response.raise_for_status()
            return response
        except Exception as e:
            raise NetworkError(f"Failed to get OKMart search result: {e}")


class OKMartResponseParser:
    def __init__(self, html: str) -> None:
        self.soup = BeautifulSoup(html, "html.parser")
        self.result = {}

    def parse(self) -> dict:
        self.result["triNo"] = self._find_by_class_name("triNo")
        self.result["odNo"] = self._find_by_class_name("odNo")
        self.result["type"] = self._find_by_class_name("type")
        self.result["status"] = self._find_by_class_name("status")
        self.result["stNo"] = self._find_by_class_name("stNo")
        self.result["stNm"] = self._find_by_class_name("stNm")
        tags = self.soup.find_all(class_="stNm")
        self.result["stNm2"] = tags[1].text if len(tags) > 1 else None
        self.result["takeFrom"] = self._find_by_class_name("takeFrom")
        self.result["takeTo"] = self._find_by_class_name("takeTo")
        self.result["takeAt"] = self._find_by_class_name("takeAt")
        self.result["taker"] = self._find_by_class_name("taker")

        return self.result

    def _find_by_class_name(self, class_name: str) -> str | None:
        tag = self.soup.find(class_=class_name)
        if tag:
            return tag.text.strip()
        else:
            return None


class OKMartTrackingInfoAdapter(TrackingInfoAdapter):
    @staticmethod
    def convert(raw_data: Any, order_id: str | None = None) -> TrackingInfo | None:
        if not raw_data or raw_data.get("odNo") is None:
            return None

        oid = raw_data["odNo"]
        status = raw_data["status"]
        is_delivered = raw_data["status"] == "已送達" or raw_data["status"] == "已取貨"
        time_val = raw_data.get("takeFrom") or raw_data.get("takeAt")

        return TrackingInfo(
            order_id=oid,
            platform=Platform.OKMart.value,
            time=time_val,
            status=status,
            is_delivered=is_delivered,
            raw_data=raw_data,
        )
