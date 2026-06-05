import logging
from typing import Final, Any

import httpx
from bs4 import BeautifulSoup
import charset_normalizer

from .base import Tracker, TrackingInfo, RequestHandler, TrackingInfoAdapter, NetworkError
from .enums import Platform

BASE_URL: Final = "https://query2.e-can.com.tw/ECAN_APP/DS_LINK.asp"


class EcanTracker(Tracker):
    def __init__(self):
        self.tracking_info = None

    def track_status(self, tracking_number: str) -> TrackingInfo | None:
        data = EcanRequestHandler().get_data(tracking_number)
        self.tracking_info = EcanTrackingInfoAdapter.convert(data, tracking_number)
        return self.tracking_info

    async def track_status_async(self, tracking_number: str) -> TrackingInfo | None:
        data = await EcanRequestHandler().get_data_async(tracking_number)
        self.tracking_info = EcanTrackingInfoAdapter.convert(data, tracking_number)
        return self.tracking_info


class EcanRequestHandler(RequestHandler):
    def get_data(self, order_id: str) -> dict:
        url = BASE_URL
        track_data = {'txtMainID': order_id, 'B1': '查詢'}
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.post(url, data=track_data)
                resp.raise_for_status()
                encoding = charset_normalizer.detect(resp.content).get("encoding") or "utf-8"
                resp.encoding = encoding
                return {"html": resp.text}
        except Exception as e:
            raise NetworkError(f"Ecan request failed: {e}")

    async def get_data_async(self, order_id: str) -> dict:
        url = BASE_URL
        track_data = {'txtMainID': order_id, 'B1': '查詢'}
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, data=track_data)
                resp.raise_for_status()
                encoding = charset_normalizer.detect(resp.content).get("encoding") or "utf-8"
                resp.encoding = encoding
                return {"html": resp.text}
        except Exception as e:
            raise NetworkError(f"Ecan async request failed: {e}")


class EcanTrackingInfoAdapter(TrackingInfoAdapter):
    @staticmethod
    def convert(raw_data: Any, order_id: str | None = None) -> TrackingInfo | None:
        if not raw_data or "html" not in raw_data:
            return None
        soup = BeautifulSoup(raw_data["html"], "html.parser")

        table = soup.select_one("table.sheetList")
        if not table:
            return None

        waybill = None
        waybill_td = table.select_one('tbody.ListStyle01 td[colspan="4"]')
        if waybill_td:
            txt = waybill_td.get_text(strip=True)
            if "單號" in txt:
                waybill = txt.replace("單號：", "").replace("單號:", "").strip().split('-')[0]

        details = []
        for tr in table.select("tbody.ListStyle01 tr"):
            if tr.select_one('td[colspan="4"]'):
                continue

            tds = tr.find_all("td")
            if len(tds) < 4:
                continue

            time_text = tds[0].get_text(" ", strip=True)
            status = tds[1].get_text(strip=True)
            desc = tds[2].get_text(strip=True)
            station = tds[3].get_text(strip=True)

            details.append(
                {
                    "日期": time_text,
                    "狀態": status,
                    "說明": desc,
                    "作業站": station,
                    "貨物狀態": f"{status}({station})",
                    "作業時間": time_text,
                    "營業所": station,
                }
            )

        if not details:
            return None

        latest = details[-1]
        delivered_text = f'{latest.get("狀態","")} {latest.get("說明","")}'
        is_delivered = ("配達完成" in delivered_text) or ("已送達" in delivered_text) or ("完成配達" in delivered_text) or ("貨件送達" in delivered_text)

        return TrackingInfo(
            order_id=waybill or order_id or "",
            platform=Platform.Ecan.value,
            status=f'{latest.get("狀態","")}({latest.get("作業站","")}) - {latest.get("說明","")}'.strip(" -"),
            time=latest.get("日期") or latest.get("作業時間"),
            is_delivered=is_delivered,
            raw_data=details,
        )

