import io
import logging
import re
from typing import Final

import pytesseract
import requests
from bs4 import BeautifulSoup, Tag
from PIL import Image

from .base import Tracker, TrackingInfo


class SevenElevenTracker(Tracker):
    BASE_URL: Final = "https://eservice.7-11.com.tw/e-tracking/"
    SEARCH_URL: Final = BASE_URL + "search.aspx"

    def __init__(self, max_retry: int = 5):
        self.session = requests.Session()
        self.max_retry = max_retry  # max retry times for captcha

    def search(self, order_id: str) -> TrackingInfo | None:
        """Tracking order status from 7-11 e-tracking website

        :param order_id: 寄件8碼或取貨11碼、12碼
        """
        if not self._validate_order_id(order_id):
            return None

        # Try to search the order status
        retry_counter = 0
        raw_data = None
        while retry_counter < self.max_retry:
            # Get the search page
            response = self._get_search_page()
            if response is None:
                retry_counter += 1
                logging.warning(
                    f"[7-11] Failed to get the search page, Retry {retry_counter} times"
                )
                continue

            # Construct payload and send post request
            payload = self._construct_payload(response, order_id)
            response = self._send_post_request(payload)
            if response is None:
                retry_counter += 1
                logging.warning(
                    f"[7-11] Failed to send post request, Retry {retry_counter} times"
                )
                continue

            # Parse the response
            parser = SevenElevenResponseParser(response.text)
            raw_data = parser.parse()

            # Check if there is any captcha error
            if self._captcha_error(raw_data):
                retry_counter += 1
                logging.warning(f"[7-11] Captcha Error, Retry {retry_counter} times")
            else:
                break

        self.tracking_info = self._convert_to_tracking_info(raw_data)
        return self.tracking_info

    def _validate_order_id(self, order_id: str) -> bool:
        return len(order_id) == 8 or len(order_id) == 11 or len(order_id) == 12

    def _get_search_page(self) -> requests.Response | None:
        logging.info("[7-11] Getting the search page...")
        response = self.session.get(self.SEARCH_URL)
        if response.status_code != 200:
            return None
        return response

    def _construct_payload(self, response: requests.Response, order_id: str) -> dict:
        soup = BeautifulSoup(response.text, "html.parser")
        view_state = self._get_payload_value(soup, "__VIEWSTATE")
        view_state_generator = self._get_payload_value(soup, "__VIEWSTATEGENERATOR")
        validate_image = self._get_validate_image(response.text)
        code = self._get_validate_code(validate_image)
        payload = {
            "__EVENTTARGET": "submit",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": view_state,
            "__VIEWSTATEGENERATOR": view_state_generator,
            "txtProductNum": order_id,
            "tbChkCode": code,
            "txtIMGName": "",
            "txtPage": 1,
        }
        return payload

    def _get_payload_value(self, soup: BeautifulSoup, key: str) -> str | None:
        tag = soup.find("input", id=key)
        if isinstance(tag, Tag):
            return tag.get("value")
        else:
            return None

    def _get_validate_image(self, html) -> Image.Image:
        """Get validate image from 7-11 e-tracking website"""
        validate_image_url = ""
        url_suffix = re.search(r'src="(ValidateImage\.aspx\?ts=[0-9]+)"', html)
        if url_suffix is not None:
            validate_image_url = self.BASE_URL + url_suffix.group(1)

        response = self.session.get(validate_image_url)
        return Image.open(io.BytesIO(response.content))

    def _get_validate_code(self, image: Image.Image) -> str:
        tesseract_config = "-c tessedit_char_whitelist=0123456789 --psm 8"
        code = pytesseract.image_to_string(image, config=tesseract_config).strip()
        return code

    def _send_post_request(self, payload: dict) -> requests.Response | None:
        logging.info("[7-11] Sending post request to the search page...")
        response = self.session.post(self.SEARCH_URL, data=payload)
        if response.status_code != 200:
            return None
        return response

    def _captcha_error(self, raw_data: dict) -> bool:
        return raw_data["msg"] == "驗證碼錯誤!!"

    def _convert_to_tracking_info(self, raw_data: dict | None) -> TrackingInfo | None:
        if raw_data is None or raw_data["result"]["info"] is None:
            return None

        order_id = raw_data["result"]["info"]["query_no"]

        # Extract status and time from m_news
        pattern = r"(.*)(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})"
        match_obj = re.match(pattern, raw_data["m_news"])
        if match_obj is not None:
            status = match_obj.group(1)
            time = match_obj.group(2)
        else:
            return None

        is_delivered = "包裹配達取件門市" in status or "已完成包裹成功取件" in status

        return TrackingInfo(
            order_id=order_id,
            platform="7-11",
            status=status,
            time=time,
            is_delivered=is_delivered,
            raw_data=raw_data,
        )


class SevenElevenResponseParser:
    def __init__(self, html: str):
        """Parser for 7-11 e-tracking response

        :param html: html content
        """
        self.soup = BeautifulSoup(html, "html.parser")
        self.result = {
            "msg": None,
            "m_news": None,
            "result": {"info": None, "shipping": None},
        }

    def parse(self) -> dict:
        """Parse the response and extract the information"""

        # Check if there is any alert message in the script tag
        script_tags = self.soup.find_all("script")
        for tag in script_tags:
            text = tag.get_text()
            if "alert(" in text:
                self.result["msg"] = self._extract_alert_message(text)
                return self.result

        # Check if there is any error message
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
