import json
import re
from datetime import datetime
from typing import Any, Final

import httpx

from .base import NetworkError, RequestHandler, Tracker, TrackingInfo, TrackingInfoAdapter
from .enums import Platform

TRACKING_URL: Final = "https://www.25431010.tw/tracking"
SERVER_ACTION_ID: Final = "404b6e8c1db61bb0b4615ae0a01c3cde3ddd5f3215"
DELIVERED_KEYWORDS: Final = ("已送達", "送達", "配送完成", "配達", "簽收", "已完成")


class BianLiDaiTracker(Tracker):
    def __init__(self):
        self.tracking_info = None

    def normalize_order_id(self, order_id: str) -> str | None:
        value = super().normalize_order_id(order_id)
        if value is None or not 10 <= len(value) <= 12:
            return None
        return value

    def track_status(self, order_id: str) -> TrackingInfo | None:
        order_id = self.normalize_order_id(order_id)
        if order_id is None:
            return None
        data = BianLiDaiRequestHandler().get_data(order_id)
        self.tracking_info = BianLiDaiTrackingInfoAdapter.convert(data, order_id)
        return self.tracking_info

    async def track_status_async(self, order_id: str) -> TrackingInfo | None:
        order_id = self.normalize_order_id(order_id)
        if order_id is None:
            return None
        data = await BianLiDaiRequestHandler().get_data_async(order_id)
        self.tracking_info = BianLiDaiTrackingInfoAdapter.convert(data, order_id)
        return self.tracking_info


class BianLiDaiRequestHandler(RequestHandler):
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; BianLiDaiTracker/1.0)",
            "Accept": "text/x-component",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            "Content-Type": "text/plain;charset=UTF-8",
            "Next-Action": SERVER_ACTION_ID,
            "Origin": "https://www.25431010.tw",
            "Referer": TRACKING_URL,
        }

    def get_data(self, order_id: str) -> dict:
        try:
            with httpx.Client(timeout=20) as client:
                response = client.post(
                    TRACKING_URL,
                    content=json.dumps([order_id], ensure_ascii=False),
                    headers=self.headers,
                )
        except Exception as e:
            raise NetworkError(f"台灣便利帶 request failed: {e}")

        if response.status_code >= 500:
            return {"rsc": response.text, "order_id": order_id, "status_code": response.status_code}
        try:
            response.raise_for_status()
        except Exception as e:
            raise NetworkError(f"台灣便利帶 request failed: {e}")
        return {"rsc": response.text, "order_id": order_id, "status_code": response.status_code}

    async def get_data_async(self, order_id: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    TRACKING_URL,
                    content=json.dumps([order_id], ensure_ascii=False),
                    headers=self.headers,
                )
        except Exception as e:
            raise NetworkError(f"台灣便利帶 async request failed: {e}")

        if response.status_code >= 500:
            return {"rsc": response.text, "order_id": order_id, "status_code": response.status_code}
        try:
            response.raise_for_status()
        except Exception as e:
            raise NetworkError(f"台灣便利帶 async request failed: {e}")
        return {"rsc": response.text, "order_id": order_id, "status_code": response.status_code}


class BianLiDaiTrackingInfoAdapter(TrackingInfoAdapter):
    @staticmethod
    def convert(raw_data: Any, order_id: str | None = None) -> TrackingInfo | None:
        payload = _extract_payload(raw_data)
        if not payload:
            return None

        history = payload.get("history") or []
        if not isinstance(history, list) or not history:
            return None

        records = [item for item in history if isinstance(item, dict)]
        if not records:
            return None

        records = sorted(records, key=lambda item: _time_sort_key(item.get("record_at")), reverse=True)
        latest = records[0]
        status = str(latest.get("state") or "").strip()
        if not status:
            return None

        oid = str(payload.get("barcode12") or order_id or "").strip()
        if not oid or oid == "查無條碼":
            return None

        return TrackingInfo(
            order_id=oid,
            platform=Platform.BianLiDai.value,
            status=status,
            time=_normalize_time(latest.get("record_at")),
            is_delivered=any(keyword in status for keyword in DELIVERED_KEYWORDS),
            raw_data=records,
        )


def _extract_payload(raw_data: Any) -> dict | None:
    if isinstance(raw_data, dict):
        if isinstance(raw_data.get("history"), list):
            return raw_data
        if isinstance(raw_data.get("json"), dict):
            return _extract_payload(raw_data["json"])
        rsc = raw_data.get("rsc")
        if isinstance(rsc, str):
            return _extract_payload_from_rsc(rsc)

    return None


def _extract_payload_from_rsc(text: str) -> dict | None:
    for line in text.splitlines():
        _, sep, body = line.partition(":")
        if not sep:
            body = line
        body = body.strip()
        if not body or body.startswith("E"):
            continue
        try:
            value = json.loads(body)
        except json.JSONDecodeError:
            continue

        payload = _find_history_payload(value)
        if payload:
            return payload
    return None


def _find_history_payload(value: Any) -> dict | None:
    if isinstance(value, dict):
        if isinstance(value.get("history"), list):
            return value
        for child in value.values():
            payload = _find_history_payload(child)
            if payload:
                return payload
    elif isinstance(value, list):
        for child in value:
            payload = _find_history_payload(child)
            if payload:
                return payload
    return None


def _time_sort_key(value: Any) -> datetime:
    normalized = _normalize_time(value)
    if not normalized:
        return datetime.min
    for fmt in ("%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M"):
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            continue
    return datetime.min


def _normalize_time(value: Any) -> str | None:
    if not value:
        return None
    text = str(value).strip().replace("T", " ")
    text = re.sub(r"\.\d+(?:Z)?$", "", text)
    text = text.rstrip("Z")

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M"):
        try:
            dt = datetime.strptime(text, fmt)
            return dt.strftime("%Y/%m/%d %H:%M:%S")
        except ValueError:
            continue
    return text
