import io
import re
from typing import Final, Any

import ddddocr
import httpx
from bs4 import BeautifulSoup, Tag
from PIL import Image

from .base import Tracker, TrackingInfo, RequestHandler, TrackingInfoAdapter, NetworkError, CaptchaError
from .enums import Platform

BASE_URL: Final = "https://eservice.7-11.com.tw/e-tracking/"
SEARCH_URL: Final = BASE_URL + "search.aspx"


class SevenElevenTracker(Tracker):
    def __init__(self):
        self.tracking_info = None

    def track_status(self, order_id: str) -> TrackingInfo | None:
        order_id = self.normalize_order_id(order_id)
        if order_id is None:
            return None
        data = SevenElevenRequestHandler().get_data(order_id)
        self.tracking_info = SevenElevenTrackingInfoAdapter.convert(data)
        return self.tracking_info

    async def track_status_async(self, order_id: str) -> TrackingInfo | None:
        order_id = self.normalize_order_id(order_id)
        if order_id is None:
            return None
        data = await SevenElevenRequestHandler().get_data_async(order_id)
        self.tracking_info = SevenElevenTrackingInfoAdapter.convert(data)
        return self.tracking_info

    def normalize_order_id(self, order_id: str) -> str | None:
        value = super().normalize_order_id(order_id)
        if value is None or len(value) not in {8, 11, 12}:
            return None
        return value


class SevenElevenRequestHandler(RequestHandler):
    def __init__(self, max_retry: int = 5):
        self.max_retry = max_retry
        self.ocr = ddddocr.DdddOcr(show_ad=False)

    def get_data(self, order_id: str) -> dict | None:
        retry_counter = 0
        with httpx.Client(timeout=15) as client:
            while retry_counter < self.max_retry:
                try:
                    response = self._post_search(client, order_id)
                    result = SevenElevenResponseParser(response.text).parse()
                    if result["msg"] == "驗證碼錯誤!!":
                        retry_counter += 1
                        continue
                    return result
                except Exception as e:
                    if retry_counter >= self.max_retry - 1:
                        raise NetworkError(f"7-11 request failed after retries: {e}")
                    retry_counter += 1

        raise CaptchaError("Incorrect captcha after max retries")

    async def get_data_async(self, order_id: str) -> dict | None:
        retry_counter = 0
        async with httpx.AsyncClient(timeout=15) as client:
            while retry_counter < self.max_retry:
                try:
                    response = await self._post_search_async(client, order_id)
                    result = SevenElevenResponseParser(response.text).parse()
                    if result["msg"] == "驗證碼錯誤!!":
                        retry_counter += 1
                        continue
                    return result
                except Exception as e:
                    if retry_counter >= self.max_retry - 1:
                        raise NetworkError(f"7-11 async request failed after retries: {e}")
                    retry_counter += 1

        raise CaptchaError("Incorrect captcha after max retries")

    def _post_search(self, client: httpx.Client, order_id: str) -> httpx.Response:
        response = client.get(SEARCH_URL)
        if response.status_code != 200:
            raise NetworkError("Failed to get search page")

        payload = self._construct_payload(client, response, order_id)
        response = client.post(SEARCH_URL, data=payload)
        if response.status_code != 200:
            raise NetworkError("Failed to post search request")
        return response

    async def _post_search_async(self, client: httpx.AsyncClient, order_id: str) -> httpx.Response:
        response = await client.get(SEARCH_URL)
        if response.status_code != 200:
            raise NetworkError("Failed to get search page")

        payload = await self._construct_payload_async(client, response, order_id)
        response = await client.post(SEARCH_URL, data=payload)
        if response.status_code != 200:
            raise NetworkError("Failed to post search request")
        return response

    def _construct_payload(self, client: httpx.Client, response: httpx.Response, order_id: str) -> dict:
        soup = BeautifulSoup(response.text, "html.parser")
        view_state = self._find_value_by_id(soup, "__VIEWSTATE")
        view_state_generator = self._find_value_by_id(soup, "__VIEWSTATEGENERATOR")
        validate_code = self._get_validate_code(client, response.text)
        return {
            "__EVENTTARGET": "submit",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": view_state,
            "__VIEWSTATEGENERATOR": view_state_generator,
            "txtProductNum": order_id,
            "tbChkCode": validate_code,
            "txtIMGName": "",
            "txtPage": 1,
        }

    async def _construct_payload_async(self, client: httpx.AsyncClient, response: httpx.Response, order_id: str) -> dict:
        soup = BeautifulSoup(response.text, "html.parser")
        view_state = self._find_value_by_id(soup, "__VIEWSTATE")
        view_state_generator = self._find_value_by_id(soup, "__VIEWSTATEGENERATOR")
        validate_code = await self._get_validate_code_async(client, response.text)
        return {
            "__EVENTTARGET": "submit",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": view_state,
            "__VIEWSTATEGENERATOR": view_state_generator,
            "txtProductNum": order_id,
            "tbChkCode": validate_code,
            "txtIMGName": "",
            "txtPage": 1,
        }

    def _get_validate_code(self, client: httpx.Client, html: str) -> str:
        validate_image = self._get_validate_image(client, html)
        return self.ocr.classification(validate_image)

    async def _get_validate_code_async(self, client: httpx.AsyncClient, html: str) -> str:
        validate_image = await self._get_validate_image_async(client, html)
        return self.ocr.classification(validate_image)

    def _get_validate_image(self, client: httpx.Client, html: str) -> Image.Image:
        url_suffix = re.search(r'src="(ValidateImage\.aspx\?ts=[0-9]+)"', html)
        if url_suffix is None:
            raise CaptchaError("Failed to get validate image url")
        img_url = BASE_URL + url_suffix.group(1)
        response = client.get(img_url)
        if response.status_code != 200:
            raise NetworkError("Failed to get validate image")
        return Image.open(io.BytesIO(response.content))

    async def _get_validate_image_async(self, client: httpx.AsyncClient, html: str) -> Image.Image:
        url_suffix = re.search(r'src="(ValidateImage\.aspx\?ts=[0-9]+)"', html)
        if url_suffix is None:
            raise CaptchaError("Failed to get validate image url")
        img_url = BASE_URL + url_suffix.group(1)
        response = await client.get(img_url)
        if response.status_code != 200:
            raise NetworkError("Failed to get validate image")
        return Image.open(io.BytesIO(response.content))

    def _find_value_by_id(self, soup: BeautifulSoup, id: str) -> str | None:
        tag = soup.find("input", id=id)
        if isinstance(tag, Tag):
            value = tag.get("value")
            if isinstance(value, str):
                return value
        return None


class SevenElevenResponseParser:
    def __init__(self, html: str):
        self.soup = BeautifulSoup(html, "html.parser")
        self.result = {
            "msg": None,
            "m_news": None,
            "result": {"info": None, "shipping": None},
        }

    def parse(self) -> dict:
        script_tags = self.soup.find_all("script")
        for tag in script_tags:
            text = tag.get_text()
            if "alert(" in text:
                self.result["msg"] = self._extract_alert_message(text)
                return self.result

        error_message = self.soup.find("span", id="lbMsg")
        if error_message is not None:
            self.result["msg"] = error_message.get_text()
            return self.result

        self.result["m_news"] = self._extract_m_news_message()
        self.result["result"]["info"] = self._extract_info_message()
        self.result["result"]["shipping"] = self._extract_shipping_message()
        self.result["msg"] = "success"

        return self.result

    def _extract_alert_message(self, text: str) -> str:
        return text.split("alert('")[1].split("');")[0]

    def _extract_m_news_message(self) -> str:
        m_news = self.soup.find("div", {"class": "m_news"})
        if isinstance(m_news, Tag):
            return m_news.get_text()
        else:
            return ""

    def _extract_info_message(self) -> dict:
        res = {}
        info_tag = self.soup.find("div", class_="info")
        if isinstance(info_tag, Tag):
            infos = info_tag.find_all("span")
            for info in infos:
                res[info.get("id")] = info.get_text()

            service_type = info_tag.find("h4", id="servicetype")
            if service_type is not None:
                res["servicetype"] = service_type.get_text()
        return res

    def _extract_shipping_message(self) -> list:
        res = []
        shipping_tag = self.soup.find("div", class_="shipping")
        if isinstance(shipping_tag, Tag):
            shippings = shipping_tag.find_all("p")
            for shipping in shippings:
                res.append(shipping.get_text())
        return res


class SevenElevenTrackingInfoAdapter(TrackingInfoAdapter):
    @staticmethod
    def convert(raw_data: Any, order_id: str | None = None) -> TrackingInfo | None:
        if raw_data is None or raw_data.get("result") is None or raw_data["result"].get("info") is None:
            return None

        oid = raw_data["result"]["info"]["query_no"]

        pattern = r"(.*)(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})"
        match_obj = re.match(pattern, raw_data["m_news"])
        if match_obj is not None:
            status = match_obj.group(1)
            time_val = match_obj.group(2)
        else:
            return None

        is_delivered = "包裹配達取件門市" in status or "已完成包裹成功取件" in status

        return TrackingInfo(
            order_id=oid,
            platform=Platform.SevenEleven.value,
            status=status,
            time=time_val,
            is_delivered=is_delivered,
            raw_data=raw_data,
        )
