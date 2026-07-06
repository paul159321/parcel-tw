import logging
from typing import Final, Any

import httpx

from .base import Tracker, TrackingInfo, RequestHandler, TrackingInfoAdapter, NetworkError
from .enums import Platform

BASE_URL: Final = "https://postserv.post.gov.tw/pstmail/EsoafDispatcher"


class PstTracker(Tracker):
    def __init__(self):
        self.tracking_info = None

    def track_status(self, tracking_number: str) -> TrackingInfo | None:
        tracking_number = self.normalize_order_id(tracking_number)
        if tracking_number is None:
            return None
        data = PstRequestHandler().get_data(tracking_number)
        self.tracking_info = PstTrackingInfoAdapter.convert(data, tracking_number)
        return self.tracking_info

    async def track_status_async(self, tracking_number: str) -> TrackingInfo | None:
        tracking_number = self.normalize_order_id(tracking_number)
        if tracking_number is None:
            return None
        data = await PstRequestHandler().get_data_async(tracking_number)
        self.tracking_info = PstTrackingInfoAdapter.convert(data, tracking_number)
        return self.tracking_info


class PstRequestHandler(RequestHandler):
    def get_data(self, order_id: str) -> dict:
        payload = self._construct_payload(order_id)
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.post(BASE_URL, json=payload)
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            raise NetworkError(f"Pstmail request failed: {e}")

    async def get_data_async(self, order_id: str) -> dict:
        payload = self._construct_payload(order_id)
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(BASE_URL, json=payload)
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            raise NetworkError(f"Pstmail async request failed: {e}")

    def _construct_payload(self, order_id: str) -> dict:
        return {
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
                "MAILNO": order_id,
                "pageCount": 10,
            },
        }


class PstTrackingInfoAdapter(TrackingInfoAdapter):
    @staticmethod
    def convert(raw_data: Any, order_id: str | None = None) -> TrackingInfo | None:
        if not raw_data or not isinstance(raw_data, list) or len(raw_data) == 0:
            return None
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
            order_id=order_id or "",
            platform=Platform.Pst.value,
            status=latest["貨物狀態"],
            time=latest["作業時間"],
            is_delivered=any(
                k in latest.get("貨物狀態", "")
                for k in ("投遞成功", "投遞完成", "已簽收", "送達")
            ),
            raw_data=details,
        )
