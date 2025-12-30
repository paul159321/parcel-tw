import logging
from typing import Final

import requests
from bs4 import BeautifulSoup

from .base import Tracker, TrackingInfo
from .enums import Platform

BASE_URL: Final = "https://www.t-cat.com.tw/Inquire/TraceDetail.aspx?BillID={waybill}"


class TcatTracker(Tracker):
    def __init__(self):
        self.tracking_info = None

    def track_status(self, tracking_number: str) -> TrackingInfo | None:
        try:
            data = TcatRequestHandler().get_data(tracking_number)
        except Exception as e:
            logging.error(f"[Tcat] {e}")
            return None

        #logging.info("[Tcat] Parsing the response...")
        self.tracking_info = TcatTrackingInfoAdapter.convert(tracking_number, data)

        return self.tracking_info


class TcatRequestHandler:
    def __init__(self):
        self.session = requests.Session()

    def get_data(self, tracking_number: str) -> dict:
        url = BASE_URL.format(waybill=tracking_number)
        try:
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            raise Exception(f"請求失敗: {e}")

        return {"html": resp.text}


class TcatTrackingInfoAdapter:
    @staticmethod
    def convert(tracking_number: str, raw_data: dict) -> TrackingInfo | None:
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
            order_id=waybill or tracking_number,
            platform=Platform.Tcat.value,
            status=latest["貨物狀態"],
            time=latest["作業時間"],
            is_delivered=any(k in latest.get("貨物狀態", "") for k in ("配達完成", "送達")),
            raw_data=details,
        )
