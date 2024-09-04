import logging
import re
from typing import Final

import requests
from bs4 import BeautifulSoup

from .base import Tracker, TrackingInfo


class OKMartTracker(Tracker):
    VALIDATE_URL: Final = "https://ecservice.okmart.com.tw/Tracking/ValidateNumber.ashx"
    RESULT_URL: Final = "https://ecservice.okmart.com.tw/Tracking/Result"

    def __init__(self) -> None:
        self.session = requests.Session()
        self.tracking_info = None

    def search(self, order_id: str) -> TrackingInfo | None:
        """Track the package status of OKMart by order_id"""

        logging.info("[OKMart] Getting validate code")
        validate_code = self._get_validate_code()

        if validate_code is None:
            logging.error("[OKMart] Failed to get validate code")
            return None

        logging.info("[OKMart] Getting the search result")
        response = self._get_search_result(order_id, validate_code)

        logging.info("[OKMart] Parsing the response")
        parser = OKMartResponseParser(response.text)
        raw_data = parser.parse()

        self.tracking_info = self._convert_to_tracking_info(raw_data)

        return self.tracking_info

    def _get_validate_code(self) -> str | None:
        response = self.session.get(self.VALIDATE_URL)

        cookie = response.headers["Set-Cookie"]
        matchobj = re.search(r"ValidateNumber=code=(.....); path=/", cookie)
        if matchobj:
            return matchobj.group(1)

    def _get_search_result(
        self, order_id: str, validate_code: str
    ) -> requests.Response:
        headers = {
            "Cookie": f"ValidateNumber=code={validate_code}&odno={order_id}&cutknm=&cutktl="
        }
        params = {"inputOdNo": order_id, "inputCode1": validate_code}

        response = self.session.get(self.RESULT_URL, params=params, headers=headers)
        return response

    def _convert_to_tracking_info(self, raw_data: dict) -> TrackingInfo | None:
        if raw_data["odNo"] is None:
            return None

        order_id = raw_data["odNo"]
        status = raw_data["status"]
        # TODO: Check the message of status is arrived
        is_arrived = raw_data["status"] == "已送達" or raw_data["status"] == "已取貨"

        return TrackingInfo(
            order_id=order_id,
            platform="OKMart",
            time=None,
            status=status,
            is_arrived=is_arrived,
            raw_data=raw_data,
        )


class OKMartResponseParser:
    def __init__(self, html: str) -> None:
        self.soup = BeautifulSoup(html, "html.parser")
        self.result = {}

    def parse(self) -> dict:
        self.result["triNo"] = self._find_by_class_name("triNo")  # 寄件編號
        self.result["odNo"] = self._find_by_class_name("odNo")  # 訂單編號
        self.result["type"] = self._find_by_class_name("type")  # 類別
        self.result["status"] = self._find_by_class_name("status")  # 目前貨況
        self.result["stNo"] = self._find_by_class_name("stNo")  # 取件門市店號
        self.result["stNm"] = self._find_by_class_name("stNm")  # 取件門市名稱
        tags = self.soup.find_all(class_="stNm")
        self.result["stNm2"] = tags[1].text if len(tags) > 1 else None  # 取件門市地址
        self.result["takeFrom"] = self._find_by_class_name("takeFrom")  # 貨到門市日期
        self.result["takeTo"] = self._find_by_class_name("takeTo")  # 取貨截止
        self.result["takeAt"] = self._find_by_class_name("takeAt")  # 取貨日期
        self.result["taker"] = self._find_by_class_name("taker")  # 取件人

        return self.result

    def _find_by_class_name(self, class_name: str) -> str | None:
        tag = self.soup.find(class_=class_name)
        if tag:
            return tag.text.strip()
        else:
            return None
