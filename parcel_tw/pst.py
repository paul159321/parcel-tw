import logging
from typing import Final

import requests

from .base import Tracker, TrackingInfo
from .enums import Platform

BASE_URL: Final = "https://postserv.post.gov.tw/pstmail/EsoafDispatcher"


class PstTracker(Tracker):
    def __init__(self):
        self.tracking_info = None

    def track_status(self, tracking_number: str) -> TrackingInfo | None:
        try:
            data = PstRequestHandler().get_data(tracking_number)
        except Exception as e:
            logging.error(f"[Pstmail] {e}")
            return None

        self.tracking_info = PstTrackingInfoAdapter.convert(
            tracking_number, data
        )

        return self.tracking_info


class PstRequestHandler:
    def __init__(self):
        self.session = requests.Session()

    def get_data(self, tracking_number: str) -> dict:
        payload = {
            "header": {
                "InputVOClass": "com.systex.jbranch.app.server.post.vo.EB500100InputVO",
                "TxnCode": "EB500100",
                "BizCode": "query2",
                "StampTime": True,
                "SupvPwd": "",
                "TXN_DATA": {},
                "SupvID": "",
                "CustID": "",
                "REQUEST_ID": "",
                "ClientTransaction": True,
                "DevMode": False,
                "SectionID": "esoaf",
            },
            "body": {
                "MAILNO": tracking_number,
                "pageCount": 10,
            },
        }

        try:
            resp = self.session.post(
                BASE_URL,
                json=payload,
                timeout=15,
            )
            resp.raise_for_status()
        except Exception as e:
            raise Exception(f"請求失敗: {e}")

        return resp.json()


class PstTrackingInfoAdapter:
    @staticmethod
    def convert(
        tracking_number: str,
        raw_data: list,
    ) -> TrackingInfo | None:
        try:
            items = raw_data[0]["body"]["host_rs"]["ITEM"]
        except Exception:
            return None

        if not items:
            return None

        details = []

        for item in items:
            status = item.get("STATUS", "").strip()
            station = item.get("BRHNC", "").strip()
            dt = item.get("DATIME", "").strip()

            details.append(
                {
                    "貨物狀態": f"{status}({station})",
                    "作業時間": dt,
                    "營業所": station,
                }
            )

        if not details:
            return None

        latest = details[0]

        return TrackingInfo(
            order_id=tracking_number,
            platform=Platform.Pst.value,
            status=latest["貨物狀態"],
            time=latest["作業時間"],
            is_delivered=any(
                k in latest.get("貨物狀態", "")
                for k in ("投遞成功", "投遞完成", "已簽收", "送達")
            ),
            raw_data=details,
        )