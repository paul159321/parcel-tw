import logging
from typing import Final

import requests
from bs4 import BeautifulSoup

from .base import Tracker, TrackingInfo
from .enums import Platform

BASE_URL: Final = "https://query2.e-can.com.tw/ECAN_APP/DS_LINK.asp"


class EcanTracker(Tracker):
    def __init__(self):
        self.tracking_info = None

    def track_status(self, tracking_number: str) -> TrackingInfo | None:
        try:
            data = EcanRequestHandler().get_data(tracking_number)
        except Exception as e:
            logging.error(f"[Ecan] {e}")
            return None

        #logging.info("[Ecan] Parsing the response...")
        self.tracking_info = EcanTrackingInfoAdapter.convert(tracking_number, data)

        return self.tracking_info


class EcanRequestHandler:
    def __init__(self):
        self.session = requests.Session()

    def get_data(self, tracking_number: str) -> dict:
        url = BASE_URL
        track_data = {'txtMainID':tracking_number,'B1':'查詢'}
        
        try:
            resp = self.session.post(url, data=track_data, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            raise Exception(f"請求失敗: {e}")

        # ✅ 建議：先用 apparent_encoding
        resp.encoding = resp.apparent_encoding
        return {"html": resp.text}


class EcanTrackingInfoAdapter:
    @staticmethod
    def convert(tracking_number: str, raw_data: dict) -> TrackingInfo | None:
        soup = BeautifulSoup(raw_data["html"], "html.parser")

        table = soup.select_one("table.sheetList")
        if not table:
            return None

        # 1) 取單號：在第一個 tbody.ListStyle01 的 td[colspan=4]，例如 "單號：577293125651-001"
        waybill = None
        waybill_td = table.select_one('tbody.ListStyle01 td[colspan="4"]')
        if waybill_td:
            txt = waybill_td.get_text(strip=True)
            # 可能是「單號：xxxx」或「單號:xxxx」
            if "單號" in txt:
                waybill = txt.replace("單號：", "").replace("單號:", "").strip().split('-')[0]

        # 2) 取事件列：所有 tbody.ListStyle01 裡的 tr，但要排除那個 colspan=4 的單號列
        details = []
        for tr in table.select("tbody.ListStyle01 tr"):
            # 排除單號列
            if tr.select_one('td[colspan="4"]'):
                continue

            tds = tr.find_all("td")
            if len(tds) < 4:
                continue

            # 日期欄通常包在 <span class="date">2025/12/19 14:42</span>
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
                    # 你原本的 key 也想保留可以：
                    "貨物狀態": f"{status}({station})",
                    "作業時間": time_text,
                    "營業所": station,
                }
            )

        if not details:
            return None

        # ✅ 如果你確認網站是「由舊到新」排序，請改用下面排序後取最後一筆
        # from datetime import datetime
        # def parse_dt(s: str):
        #     for fmt in ("%Y/%m/%d %H:%M", "%Y/%m/%d %H:%M:%S"):
        #         try:
        #             return datetime.strptime(s, fmt)
        #         except ValueError:
        #             pass
        #     return None
        # details_sorted = sorted(
        #     details,
        #     key=lambda x: (parse_dt(x["日期"]) is None, parse_dt(x["日期"]) or datetime.min),
        # )
        # latest = details_sorted[-1]

        # 預設：網站通常最新在最上面
        latest = details[0]

        # delivered 判斷：可能出現在「狀態」或「說明」
        delivered_text = f'{latest.get("狀態","")} {latest.get("說明","")}'
        is_delivered = ("配達完成" in delivered_text) or ("已送達" in delivered_text) or ("完成配達" in delivered_text) or ("貨件送達" in delivered_text)

        return TrackingInfo(
            order_id=waybill or tracking_number,
            platform=Platform.Ecan.value,
            status=f'{latest.get("狀態","")}({latest.get("作業站","")}) - {latest.get("說明","")}'.strip(" -"),
            time=latest.get("日期") or latest.get("作業時間"),
            is_delivered=is_delivered,
            raw_data=details,
        )

