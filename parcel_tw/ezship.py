import re
from typing import Any, Final

import httpx
from bs4 import BeautifulSoup

from .base import NetworkError, RequestHandler, Tracker, TrackingInfo, TrackingInfoAdapter
from .enums import Platform

SEARCH_URL: Final = "https://www.ezship.com.tw/receiver_query/ezship_query_single_data.jsp"
REFERER: Final = "https://www.ezship.com.tw/receiver_query/ezship_query_shipstatus_2017.jsp"

DATE_PATTERN = re.compile(r"\d{4}[/-]\d{1,2}[/-]\d{1,2}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?")
DELIVERED_KEYWORDS = ("已取件", "已送達", "取件完成", "取貨完成", "配達", "貨件已領取")
STATUS_KEYS = ("狀態", "貨況", "配送", "處理", "說明")
TIME_KEYS = ("日期", "時間", "更新")


class EzShipTracker(Tracker):
    def __init__(self):
        self.tracking_info = None

    def normalize_order_id(self, order_id: str) -> str | None:
        value = super().normalize_order_id(order_id)
        if value is None or len(value) > 11:
            return None
        return value

    def track_status(self, order_id: str) -> TrackingInfo | None:
        order_id = self.normalize_order_id(order_id)
        if order_id is None:
            return None
        data = EzShipRequestHandler().get_data(order_id)
        self.tracking_info = EzShipTrackingInfoAdapter.convert(data, order_id)
        return self.tracking_info

    async def track_status_async(self, order_id: str) -> TrackingInfo | None:
        order_id = self.normalize_order_id(order_id)
        if order_id is None:
            return None
        data = await EzShipRequestHandler().get_data_async(order_id)
        self.tracking_info = EzShipTrackingInfoAdapter.convert(data, order_id)
        return self.tracking_info


class HiLifeTracker(Tracker):
    def __init__(self):
        self.tracking_info = None

    def normalize_order_id(self, order_id: str) -> str | None:
        value = super().normalize_order_id(order_id)
        if value is None or len(value) > 11:
            return None
        return value

    def track_status(self, order_id: str) -> TrackingInfo | None:
        order_id = self.normalize_order_id(order_id)
        if order_id is None:
            return None
        data = EzShipRequestHandler().get_data(order_id)
        self.tracking_info = HiLifeTrackingInfoAdapter.convert(data, order_id)
        return self.tracking_info

    async def track_status_async(self, order_id: str) -> TrackingInfo | None:
        order_id = self.normalize_order_id(order_id)
        if order_id is None:
            return None
        data = await EzShipRequestHandler().get_data_async(order_id)
        self.tracking_info = HiLifeTrackingInfoAdapter.convert(data, order_id)
        return self.tracking_info


class EzShipRequestHandler(RequestHandler):
    def get_data(self, order_id: str) -> dict:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; EzShipTracker/1.0)",
            "Referer": REFERER,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        try:
            with httpx.Client(timeout=15) as client:
                response = client.post(SEARCH_URL, data={"vSnID": order_id}, headers=headers)
                response.raise_for_status()
                return {"html": response.text, "order_id": order_id}
        except Exception as e:
            raise NetworkError(f"ezShip request failed: {e}")

    async def get_data_async(self, order_id: str) -> dict:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; EzShipTracker/1.0)",
            "Referer": REFERER,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(SEARCH_URL, data={"vSnID": order_id}, headers=headers)
                response.raise_for_status()
                return {"html": response.text, "order_id": order_id}
        except Exception as e:
            raise NetworkError(f"ezShip async request failed: {e}")


class EzShipTrackingInfoAdapter(TrackingInfoAdapter):
    @staticmethod
    def convert(raw_data: Any, order_id: str | None = None) -> TrackingInfo | None:
        return _convert_ezship(raw_data, order_id, Platform.EzShip.value)


class HiLifeTrackingInfoAdapter(TrackingInfoAdapter):
    @staticmethod
    def convert(raw_data: Any, order_id: str | None = None) -> TrackingInfo | None:
        return _convert_ezship(raw_data, order_id, Platform.HiLife.value)


def _convert_ezship(raw_data: Any, order_id: str | None, platform: str) -> TrackingInfo | None:
    if not raw_data or "html" not in raw_data:
        return None

    soup = BeautifulSoup(raw_data["html"], "html.parser")
    page_text = soup.get_text(" ", strip=True)
    if not page_text or "查無資料" in page_text:
        return None

    details = _extract_table_details(soup)
    if not details:
        details = _extract_text_details(soup)
    oid = _extract_order_id(soup, raw_data.get("order_id") or order_id, details)

    if not details:
        status = _clean_status(page_text)
        if not status:
            return None
        time_val = _extract_time(page_text)
        details = [{"貨物狀態": status, "更新時間": time_val}]

    latest = details[0]
    status = latest.get("貨物狀態") or latest.get("狀態") or _clean_status(" ".join(latest.values()))
    time_val = latest.get("更新時間") or latest.get("時間") or _extract_time(" ".join(latest.values()))
    if not status:
        return None

    return TrackingInfo(
        order_id=oid or "",
        platform=platform,
        status=status,
        time=time_val,
        is_delivered=any(keyword in status for keyword in DELIVERED_KEYWORDS),
        raw_data=details,
    )


def _extract_order_id(
    soup: BeautifulSoup, fallback: str | None, details: list[dict[str, str]]
) -> str | None:
    for detail in details:
        for key, value in detail.items():
            if any(label in key for label in ("寄件編號", "店到店編號", "店到宅編號")) and value:
                return value

    text = soup.get_text(" ", strip=True)
    match = re.search(r"(?:店到店編號|店到宅編號|寄件編號)[：:]+(\w[\w-]+)", text)
    if match:
        return match.group(1)
    return fallback


def _extract_table_details(soup: BeautifulSoup) -> list[dict[str, str]]:
    details = []
    for table in soup.find_all("table"):
        headers: list[str] = []
        for tr in table.find_all("tr"):
            cells = [cell.get_text(" ", strip=True) for cell in tr.find_all(["th", "td"])]
            cells = [cell for cell in cells if cell]
            if not cells:
                continue

            if _looks_like_header(cells):
                headers = cells
                continue

            row = _map_row(headers, cells)
            normalized = _normalize_detail_row(row)
            if normalized:
                details.append(normalized)
    return details


def _extract_text_details(soup: BeautifulSoup) -> list[dict[str, str]]:
    details = []
    for node in soup.find_all(["div", "p", "li"]):
        text = node.get_text(" ", strip=True)
        if not text or "查詢結果" in text or "備註" in text:
            continue
        if DATE_PATTERN.search(text) or any(key in text for key in STATUS_KEYS):
            status = _clean_status(text)
            if status:
                details.append({"貨物狀態": status, "更新時間": _extract_time(text)})
    return details


def _looks_like_header(cells: list[str]) -> bool:
    text = " ".join(cells)
    return any(key in text for key in STATUS_KEYS + TIME_KEYS) and not DATE_PATTERN.search(text)


def _map_row(headers: list[str], cells: list[str]) -> dict[str, str]:
    if headers and len(headers) == len(cells):
        return dict(zip(headers, cells))
    return {f"欄位{index + 1}": value for index, value in enumerate(cells)}


def _normalize_detail_row(row: dict[str, str]) -> dict[str, str] | None:
    row_text = " ".join(row.values())
    if not row_text or "查無資料" in row_text:
        return None

    status = ""
    time_val = ""
    for key, value in row.items():
        if not status and any(status_key in key for status_key in STATUS_KEYS):
            status = value
        if not time_val and any(time_key in key for time_key in TIME_KEYS):
            time_val = value

    status = status or _clean_status(row_text)
    time_val = time_val or _extract_time(row_text)
    if not status:
        return None

    normalized = {"貨物狀態": status}
    if time_val:
        normalized["更新時間"] = time_val
    normalized.update(row)
    return normalized


def _clean_status(text: str) -> str:
    status = re.sub(r"\s+", " ", text).strip()
    status = re.sub(r"^查詢結果\s*", "", status)
    status = re.sub(r"備註：.*$", "", status).strip()
    return status


def _extract_time(text: str) -> str | None:
    match = DATE_PATTERN.search(text)
    return match.group(0) if match else None
