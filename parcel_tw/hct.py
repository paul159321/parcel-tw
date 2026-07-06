import logging
import time
import random
import re
from typing import Final, Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
import ddddocr

from .base import Tracker, TrackingInfo, RequestHandler, TrackingInfoAdapter, NetworkError, CaptchaError
from .enums import Platform

SEARCH_URL: Final = "https://www.hct.com.tw/Search/SearchGoods_n.aspx"
RESULT_URL: Final = "https://www.hct.com.tw/Search/SearchGoods.aspx"
MAX_ATTEMPTS: Final = 5


class HctTracker(Tracker):
    def __init__(self):
        self.tracking_info = None

    def track_status(self, tracking_number: str) -> TrackingInfo | None:
        tracking_number = self.normalize_order_id(tracking_number)
        if tracking_number is None:
            return None
        data = HctRequestHandler(reuse_session=False).get_data(tracking_number)
        self.tracking_info = HctTrackingInfoAdapter.convert(data, tracking_number)
        return self.tracking_info

    async def track_status_async(self, tracking_number: str) -> TrackingInfo | None:
        tracking_number = self.normalize_order_id(tracking_number)
        if tracking_number is None:
            return None
        data = await HctRequestHandler(reuse_session=False).get_data_async(tracking_number)
        self.tracking_info = HctTrackingInfoAdapter.convert(data, tracking_number)
        return self.tracking_info


class HctRequestHandler(RequestHandler):
    def __init__(self, reuse_session: bool = True):
        self.reuse_session = reuse_session
        self.ocr = ddddocr.DdddOcr(show_ad=False)
        self.default_headers = {
            "User-Agent": "Mozilla/5.0 (compatible; HctTracker/1.0)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        }

    def _random_delay(self):
        time.sleep(random.uniform(0.5, 1.5))

    def _extract_tokens(self, soup: BeautifulSoup) -> dict | None:
        vs = soup.select_one('input[id="__VIEWSTATE"]')
        if not vs or not vs.get("value"):
            return None

        vsg = soup.select_one('input[id="__VIEWSTATEGENERATOR"]')
        ev = soup.select_one('input[id="__EVENTVALIDATION"]')

        return {
            "__VIEWSTATE": vs["value"],
            "__VIEWSTATEGENERATOR": vsg["value"] if vsg and vsg.get("value") else None,
            "__EVENTVALIDATION": ev["value"] if ev and ev.get("value") else None,
        }

    def _find_captcha_img(self, soup: BeautifulSoup):
        return soup.select_one(
            'img[name="imgCode"], img#imgCode, img[src*="imgCode"], img[src*="code"]'
        )

    def _get_captcha_and_tokens(self, client: httpx.Client) -> tuple[dict, str]:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                resp = client.get(SEARCH_URL, timeout=10, follow_redirects=False)
            except Exception as e:
                logging.warning(f"[HCT] SEARCH_URL 例外（第 {attempt} 次）: {e}")
                self._random_delay()
                continue

            if 300 <= resp.status_code < 400:
                logging.warning(f"[HCT] SEARCH_URL redirect（第 {attempt} 次）, status={resp.status_code}")
                self._random_delay()
                continue

            if resp.status_code != 200 or not resp.content:
                logging.warning(f"[HCT] SEARCH_URL 回傳異常（第 {attempt} 次）, status={resp.status_code}")
                self._random_delay()
                continue

            soup = BeautifulSoup(resp.content, "html.parser")
            tokens = self._extract_tokens(soup)
            img_tag = self._find_captcha_img(soup)

            if not tokens or not img_tag or not img_tag.get("src"):
                logging.warning(f"[HCT] 缺少 WebForm token 或 captcha（第 {attempt} 次）")
                self._random_delay()
                continue

            img_url = urljoin(SEARCH_URL, img_tag["src"])
            try:
                img_resp = client.get(img_url, timeout=10)
            except Exception as e:
                logging.warning(f"[HCT] captcha 下載失敗（第 {attempt} 次）: {e}")
                self._random_delay()
                continue

            if img_resp.status_code != 200 or not img_resp.content:
                logging.warning(f"[HCT] captcha 回傳異常（第 {attempt} 次）, status={img_resp.status_code}")
                self._random_delay()
                continue

            try:
                captcha = self.ocr.classification(img_resp.content)
            except Exception as e:
                logging.warning(f"[HCT] OCR 失敗（第 {attempt} 次）: {e}")
                self._random_delay()
                continue

            if isinstance(captcha, str):
                captcha = captcha.strip()

            if isinstance(captcha, str) and len(captcha) == 4:
                return tokens, captcha

            logging.warning(f"[HCT] OCR 結果不合法（{captcha}）（第 {attempt} 次）")
            self._random_delay()

        raise CaptchaError("超過最大嘗試次數，無法取得有效驗證碼")

    async def _get_captcha_and_tokens_async(self, client: httpx.AsyncClient) -> tuple[dict, str]:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                resp = await client.get(SEARCH_URL, timeout=10, follow_redirects=False)
            except Exception as e:
                logging.warning(f"[HCT] SEARCH_URL 例外（第 {attempt} 次）: {e}")
                self._random_delay()
                continue

            if 300 <= resp.status_code < 400:
                logging.warning(f"[HCT] SEARCH_URL redirect（第 {attempt} 次）, status={resp.status_code}")
                self._random_delay()
                continue

            if resp.status_code != 200 or not resp.content:
                logging.warning(f"[HCT] SEARCH_URL 回傳異常（第 {attempt} 次）, status={resp.status_code}")
                self._random_delay()
                continue

            soup = BeautifulSoup(resp.content, "html.parser")
            tokens = self._extract_tokens(soup)
            img_tag = self._find_captcha_img(soup)

            if not tokens or not img_tag or not img_tag.get("src"):
                logging.warning(f"[HCT] 缺少 WebForm token 或 captcha（第 {attempt} 次）")
                self._random_delay()
                continue

            img_url = urljoin(SEARCH_URL, img_tag["src"])
            try:
                img_resp = await client.get(img_url, timeout=10)
            except Exception as e:
                logging.warning(f"[HCT] captcha 下載失敗（第 {attempt} 次）: {e}")
                self._random_delay()
                continue

            if img_resp.status_code != 200 or not img_resp.content:
                logging.warning(f"[HCT] captcha 回傳異常（第 {attempt} 次）, status={img_resp.status_code}")
                self._random_delay()
                continue

            try:
                captcha = self.ocr.classification(img_resp.content)
            except Exception as e:
                logging.warning(f"[HCT] OCR 失敗（第 {attempt} 次）: {e}")
                self._random_delay()
                continue

            if isinstance(captcha, str):
                captcha = captcha.strip()

            if isinstance(captcha, str) and len(captcha) == 4:
                return tokens, captcha

            logging.warning(f"[HCT] OCR 結果不合法（{captcha}）（第 {attempt} 次）")
            self._random_delay()

        raise CaptchaError("超過最大嘗試次數，無法取得有效驗證碼")

    def get_data(self, order_id: str) -> dict:
        with httpx.Client(headers=self.default_headers, timeout=15) as client:
            tokens, captcha = self._get_captcha_and_tokens(client)

            middle_data = {
                "__VIEWSTATE": tokens["__VIEWSTATE"],
                "ctl00$ContentFrame$txtpKey": order_id,
                "ctl00$ContentFrame$txt_chk": captcha,
                "ctl00$ContentFrame$Button1": "查詢 >",
            }
            if tokens.get("__VIEWSTATEGENERATOR"):
                middle_data["__VIEWSTATEGENERATOR"] = tokens["__VIEWSTATEGENERATOR"]
            if tokens.get("__EVENTVALIDATION"):
                middle_data["__EVENTVALIDATION"] = tokens["__EVENTVALIDATION"]

            try:
                middle_resp = client.post(SEARCH_URL, data=middle_data, timeout=10)
                middle_resp.raise_for_status()
            except Exception as e:
                raise NetworkError(f"HCT middle search failed: {e}")

            soup = BeautifulSoup(middle_resp.content, "html.parser")
            no_tag = soup.find("input", {"name": "no"})
            chk_tag = soup.find("input", {"name": "chk"})
            if not no_tag or not chk_tag:
                raise CaptchaError("無法取得 no/chk（驗證碼錯誤或回傳非預期頁）")

            try:
                response = client.post(
                    RESULT_URL,
                    data={"no": no_tag["value"], "chk": chk_tag["value"]},
                    timeout=10,
                )
                response.raise_for_status()
            except Exception as e:
                raise NetworkError(f"HCT final search failed: {e}")

            return {"html": response.text}

    async def get_data_async(self, order_id: str) -> dict:
        async with httpx.AsyncClient(headers=self.default_headers, timeout=15) as client:
            tokens, captcha = await self._get_captcha_and_tokens_async(client)

            middle_data = {
                "__VIEWSTATE": tokens["__VIEWSTATE"],
                "ctl00$ContentFrame$txtpKey": order_id,
                "ctl00$ContentFrame$txt_chk": captcha,
                "ctl00$ContentFrame$Button1": "查詢 >",
            }
            if tokens.get("__VIEWSTATEGENERATOR"):
                middle_data["__VIEWSTATEGENERATOR"] = tokens["__VIEWSTATEGENERATOR"]
            if tokens.get("__EVENTVALIDATION"):
                middle_data["__EVENTVALIDATION"] = tokens["__EVENTVALIDATION"]

            try:
                middle_resp = await client.post(SEARCH_URL, data=middle_data, timeout=10)
                middle_resp.raise_for_status()
            except Exception as e:
                raise NetworkError(f"HCT middle search failed: {e}")

            soup = BeautifulSoup(middle_resp.content, "html.parser")
            no_tag = soup.find("input", {"name": "no"})
            chk_tag = soup.find("input", {"name": "chk"})
            if not no_tag or not chk_tag:
                raise CaptchaError("無法取得 no/chk（驗證碼錯誤或回傳非預期頁）")

            try:
                response = await client.post(
                    RESULT_URL,
                    data={"no": no_tag["value"], "chk": chk_tag["value"]},
                    timeout=10,
                )
                response.raise_for_status()
            except Exception as e:
                raise NetworkError(f"HCT final search failed: {e}")

            return {"html": response.text}


class HctTrackingInfoAdapter(TrackingInfoAdapter):
    @staticmethod
    def convert(raw_data: Any, order_id: str | None = None) -> TrackingInfo | None:
        if not raw_data or "html" not in raw_data:
            return None
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
            tooltip_attr = state_span.get("onmouseover") if state_span else ""

            tooltip_match = re.search(r"'(.*?)'", tooltip_attr)
            tooltip_text = tooltip_match.group(1) if tooltip_match else ""

            if time_text:
                records.append(
                    {
                        "作業時間": time_text,
                        "貨物狀態": (state_text + "\n" + tooltip_text).strip(),
                        "貨物件數": count_tag.get_text(strip=True).replace("件", "")
                        if count_tag
                        else "",
                        "負責營業所": office_tag.get_text(strip=True)
                        if office_tag
                        else "",
                    }
                )

        if not records:
            return None

        latest = records[0]
        return TrackingInfo(
            order_id=order_id or "",
            platform=Platform.Hct.value,
            status=latest["貨物狀態"],
            time=latest["作業時間"],
            is_delivered="送達" in latest["貨物狀態"],
            raw_data=records,
        )
