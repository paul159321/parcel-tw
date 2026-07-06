import json
import logging
import re
from datetime import datetime
from typing import Any

import httpx

from .base import Tracker, TrackingInfo, RequestHandler, TrackingInfoAdapter, NetworkError
from .enums import Platform

SEARCH_URL = "http://www.express.com.tw/Handler.aspx"


class KtjTracker(Tracker):
    def __init__(self):
        self.tracking_info = None

    def track_status(self, order_id: str) -> TrackingInfo | None:
        order_id = self.normalize_order_id(order_id)
        if order_id is None:
            return None
        raw = KtjRequestHandler().get_data(order_id)
        self.tracking_info = KtjTrackingInfoAdapter.convert(raw, order_id)
        return self.tracking_info

    async def track_status_async(self, order_id: str) -> TrackingInfo | None:
        order_id = self.normalize_order_id(order_id)
        if order_id is None:
            return None
        raw = await KtjRequestHandler().get_data_async(order_id)
        self.tracking_info = KtjTrackingInfoAdapter.convert(raw, order_id)
        return self.tracking_info


class KtjRequestHandler(RequestHandler):
    def __init__(self):
        pass

    def _warm_up_session(self, client: httpx.Client):
        url = "http://www.express.com.tw/tools/positchecking_listForKtj.aspx"
        try:
            client.get(url, timeout=10)
        except Exception:
            pass

    async def _warm_up_session_async(self, client: httpx.AsyncClient):
        url = "http://www.express.com.tw/tools/positchecking_listForKtj.aspx"
        try:
            await client.get(url, timeout=10)
        except Exception:
            pass

    def get_data(self, order_id: str) -> dict:
        headers = {
            "Accept": "text/html, */*; q=0.01",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"http://www.express.com.tw/tools/positchecking_listForKtj.aspx?searchNumber={order_id}",
        }
        payload = {
            "queryId": f'"{order_id}"',
            "Action": "getKtjData",
        }

        try:
            with httpx.Client(timeout=30) as client:
                self._warm_up_session(client)
                resp = client.post(
                    SEARCH_URL,
                    data=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                return self._parse_response(resp.text)
        except Exception as e:
            raise NetworkError(f"KTJ request failed: {e}")

    async def get_data_async(self, order_id: str) -> dict:
        headers = {
            "Accept": "text/html, */*; q=0.01",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"http://www.express.com.tw/tools/positchecking_listForKtj.aspx?searchNumber={order_id}",
        }
        payload = {
            "queryId": f'"{order_id}"',
            "Action": "getKtjData",
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                await self._warm_up_session_async(client)
                resp = await client.post(
                    SEARCH_URL,
                    data=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                return self._parse_response(resp.text)
        except Exception as e:
            raise NetworkError(f"KTJ async request failed: {e}")

    def _parse_response(self, response_text: str) -> dict:
        text = response_text.strip()
        outer = self._parse_js_object_literal(text)

        if not outer.get("success", False):
            if str(outer.get("success")).lower() not in ("true", "1"):
                raise NetworkError(f"KTJ response success=false: {outer}")

        msg = outer.get("msg")
        if not msg:
            raise NetworkError("KTJ response missing 'msg'")

        inner = json.loads(msg)
        return inner

    @staticmethod
    def _parse_js_object_literal(s: str) -> dict:
        s = s.strip()
        if s.startswith("(") and s.endswith(")"):
            s = s[1:-1].strip()
        s = re.sub(r'([{,]\s*)([A-Za-z_]\w*)(\s*:)', r'\1"\2"\3', s)
        return json.loads(s)


class KtjTrackingInfoAdapter(TrackingInfoAdapter):
    @staticmethod
    def convert(raw_data: Any, order_id: str | None = None) -> TrackingInfo | None:
        if not raw_data:
            return None
        results = raw_data.get("result") or []
        if not results:
            return None

        item = results[0] or {}
        course = item.get("course") or []
        if not course:
            return None

        latest = course[0]
        oid = item.get("bolNo") or latest.get("bolNo") or order_id

        time_str = latest.get("processCargoCrtDAteAndTime")
        if not time_str:
            d = latest.get("processCargoCrtDate")
            t = latest.get("processCargoCrtTime")
            if d and t:
                time_str = f"{d}T{t}"

        status_message = (latest.get("statusIdName") or "").strip()
        delivered_keywords = ["簽收", "配達", "已送達", "已完成配送", "已完成", "配送完成"]
        is_delivered = any(k in status_message for k in delivered_keywords)

        return TrackingInfo(
            order_id=oid,
            platform=Platform.Ktj.value,
            status=status_message,
            time=_normalize_time(time_str),
            is_delivered=is_delivered,
            raw_data=raw_data,
        )


def _normalize_time(s: str | None) -> str | None:
    if not s:
        return None

    s = s.strip()
    s = s.replace(" ", "T")
    s = re.sub(r"\.\d+$", "", s)
    if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$", s):
        s += ":00"

    try:
        dt = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return s

    return dt.strftime("%Y/%m/%d %H:%M")
