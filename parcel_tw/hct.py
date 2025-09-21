import logging
import time
import sys
from typing import Final
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import ddddocr

from .base import Tracker, TrackingInfo
from .enums import Platform

SEARCH_URL: Final = "https://www.hct.com.tw/Search/SearchGoods_n.aspx"
RESULT_URL: Final = "https://www.hct.com.tw/Search/SearchGoods.aspx"
MAX_ATTEMPTS: Final = 5


class HctTracker(Tracker):
    def __init__(self):
        self.tracking_info = None

    def track_status(self, tracking_number: str) -> TrackingInfo | None:
        try:
            data = HctRequestHandler().get_data(tracking_number)
        except Exception as e:
            logging.error(f"[HCT] {e}")
            return None

        logging.info("[HCT] Parsing the response...")
        self.tracking_info = HctTrackingInfoAdapter.convert(tracking_number, data)

        return self.tracking_info


class HctRequestHandler:
    def __init__(self):
        self.session = requests.Session()
        self.ocr = ddddocr.DdddOcr(show_ad=False)

    def _get_captcha_and_viewstate(self) -> tuple[str, str]:
        """
        嘗試取得 __VIEWSTATE 與辨識成功的驗證碼
        """
        for attempt in range(1, MAX_ATTEMPTS + 1):
            search_result = self.session.get(SEARCH_URL)
            soup = BeautifulSoup(search_result.content, "html.parser")
            vs_tag = soup.find("input", {"id": "__VIEWSTATE"})
            img_tag = soup.find("img", {"name": "imgCode"})
            if not vs_tag or not img_tag:
                logging.warning(f"[HCT] 無法取得 __VIEWSTATE 或 imgCode，重試中...")
                time.sleep(0.5)
                continue

            viewstate = vs_tag.get("value", "")
            img_url = urljoin(SEARCH_URL, img_tag["src"])
            img_resp = self.session.get(img_url)

            if img_resp.status_code != 200 or not img_resp.content:
                logging.warning(f"[HCT] 下載驗證碼失敗 (status={img_resp.status_code})，重試中...")
                time.sleep(0.5)
                continue

            captcha_text = self.ocr.classification(img_resp.content)
            if isinstance(captcha_text, str) and len(captcha_text) == 4:
                return viewstate, captcha_text

            time.sleep(0.5)

        raise Exception("超過最大嘗試次數，仍無法取得有效驗證碼")

    def get_data(self, tracking_number: str) -> dict:
        """
        從 HCT 取得完整追蹤資料 HTML
        """
        viewstate, captcha = self._get_captcha_and_viewstate()
        # 中繼查詢
        middle_data = {
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": "A6946E2E",
            "ctl00$ContentFrame$txtpKey": tracking_number,
            "ctl00$ContentFrame$txt_chk": captcha,
            "ctl00$ContentFrame$Button1": "查詢 >",
        }
        middle_response = self.session.post(SEARCH_URL, data=middle_data)
        middle_soup = BeautifulSoup(middle_response.content, "html.parser")

        no_tag = middle_soup.find("input", {"name": "no"})
        chk_tag = middle_soup.find("input", {"name": "chk"})
        if not no_tag or not chk_tag:
            raise Exception("無法從中繼回應取得 no/chk")

        no = no_tag.get("value", "")
        chk = chk_tag.get("value", "")

        # 最終查詢
        final_data = {"no": no, "chk": chk}
        response = self.session.post(RESULT_URL, data=final_data)
        if response.status_code != 200:
            raise Exception(f"查詢失敗 (status={response.status_code})")

        return {"html": response.text}


class HctTrackingInfoAdapter:
    @staticmethod
    def convert(tracking_number: str, raw_data: dict) -> TrackingInfo | None:
        """
        解析 HTML 取得物流紀錄
        """
        soup = BeautifulSoup(raw_data["html"], "html.parser")
        records = []

        for container in soup.find_all("div", class_="grid-container"):
            time_tag = container.find("div", class_="col_optime")
            state_tag = container.find("div", class_="col_state")
            state_span = state_tag.find("span", class_="linkInv") if state_tag else None
            count_tag = container.find("div", class_="col_count")
            office_tag = container.find("div", class_="col_office")

            time_text = time_tag.get_text(strip=True) if time_tag else ""
            state_text = state_span.get_text(strip=True) if state_span else ""
            count_text = ""
            if count_tag:
                count_text = count_tag.get_text(separator="", strip=True).replace("件", "").strip()
            office_text = office_tag.get_text(strip=True) if office_tag else ""

            if time_text:
                records.append(
                    {
                        "作業時間": time_text,
                        "貨物狀態": state_text,
                        "貨物件數": count_text,
                        "負責營業所": office_text,
                    }
                )

        if not records:
            return None

        latest = records[0]
        return TrackingInfo(
            order_id=tracking_number,
            platform=Platform.Hct.value,
            status=latest["貨物狀態"],
            time=latest["作業時間"],
            is_delivered="送達" in latest["貨物狀態"],
            raw_data=records,
        )
