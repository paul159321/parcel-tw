import logging
from typing import Final, Any

import httpx
from bs4 import BeautifulSoup

from .base import Tracker, TrackingInfo, RequestHandler, TrackingInfoAdapter, NetworkError
from .enums import Platform

BASE_URL: Final = "https://www.t-cat.com.tw/Inquire/TraceDetail.aspx?BillID={waybill}"


class TcatTracker(Tracker):
    def __init__(self):
        self.tracking_info = None

    def track_status(self, tracking_number: str) -> TrackingInfo | None:
        tracking_number = self.normalize_order_id(tracking_number)
        if tracking_number is None:
            return None
        data = TcatRequestHandler().get_data(tracking_number)
        self.tracking_info = TcatTrackingInfoAdapter.convert(data, tracking_number)
        return self.tracking_info

    async def track_status_async(self, tracking_number: str) -> TrackingInfo | None:
        tracking_number = self.normalize_order_id(tracking_number)
        if tracking_number is None:
            return None
        data = await TcatRequestHandler().get_data_async(tracking_number)
        self.tracking_info = TcatTrackingInfoAdapter.convert(data, tracking_number)
        return self.tracking_info


class TcatRequestHandler(RequestHandler):
    def get_data(self, order_id: str) -> dict:
        url = BASE_URL.format(waybill=order_id)
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(url)
                resp.raise_for_status()
                return {"html": resp.text}
        except Exception as e:
            raise NetworkError(f"Tcat request failed: {e}")

    async def get_data_async(self, order_id: str) -> dict:
        url = BASE_URL.format(waybill=order_id)
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                return {"html": resp.text}
        except Exception as e:
            raise NetworkError(f"Tcat async request failed: {e}")


class TcatTrackingInfoAdapter(TrackingInfoAdapter):
    @staticmethod
    def convert(raw_data: Any, order_id: str | None = None) -> TrackingInfo | None:
        if not raw_data or "html" not in raw_data:
            return None
        soup = BeautifulSoup(raw_data["html"], "html.parser")
        table = soup.select_one(".tablelist")
        if not table:
            return None

        rows = table.select("tr")
        if len(rows) <= 1:
            return None

        body_rows = rows[1:]
        details = []
        waybill = None

        for tr in body_rows:
            waybill_td = tr.select_one("td .bl12")
            if waybill_td:
                waybill = waybill_td.get_text(strip=True)

            cols = tr.select("td.style1")
            if len(cols) < 3:
                continue

            status = cols[0].get_text(strip=True)
            time_text = cols[1].get_text(separator=" ", strip=True)
            station = cols[2].get_text(strip=True)

            details.append(
                {
                    "貨物狀態": f"{status}({station})",
                    "作業時間": time_text,
                    "營業所": station,
                }
            )

        if not details:
            return None

        latest = details[0]
        return TrackingInfo(
            order_id=waybill or order_id or "",
            platform=Platform.Tcat.value,
            status=latest["貨物狀態"],
            time=latest["作業時間"],
            is_delivered=any(k in latest.get("貨物狀態", "") for k in ("配達完成", "送達")),
            raw_data=details,
        )
