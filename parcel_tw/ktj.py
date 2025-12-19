import json
import logging
import re
from datetime import datetime

from .base import Tracker, TrackingInfo, RequestHandler, TrackingInfoAdapter
from .enums import Platform

SEARCH_URL = "http://www.express.com.tw/Handler.aspx"


class KtjTracker(Tracker):
    def __init__(self):
        self.tracking_info = None

    def track_status(self, order_id: str) -> TrackingInfo | None:
        try:
            raw = KtjRequestHandler().get_data(order_id)
        except Exception as e:
            logging.error(f"[KTJ] {e}")
            return None

        self.tracking_info = KtjTrackingInfoAdapter.convert(raw)
        return self.tracking_info


class KtjRequestHandler(RequestHandler):
    def __init__(self):
        super().__init__()
        # 預先訪問一次查詢頁，建立 session cookie（非常重要）
        self._warm_up_session()

    def _warm_up_session(self):
        url = "http://www.express.com.tw/tools/positchecking_listForKtj.aspx"
        try:
            self.session.get(url, timeout=10)
        except Exception:
            pass  # 不影響後續，只是拿 cookie

    def get_data(self, order_id: str) -> dict:
        headers = {
            "Accept": "text/html, */*; q=0.01",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"http://www.express.com.tw/tools/positchecking_listForKtj.aspx?searchNumber={order_id}",
        }

        # ⚠️ queryId 要包成字串（等同 %22xxx%22）
        payload = {
            "queryId": f'"{order_id}"',
            "Action": "getKtjData",
        }

        resp = self.session.post(
            SEARCH_URL,
            data=payload,
            headers=headers,
            timeout=(5, 30),  # (連線, 讀取) → KTJ 必須拉長
        )
        resp.raise_for_status()

        return self._parse_response(resp.text)

    def _parse_response(self, response_text: str) -> dict:
        text = response_text.strip()
        outer = self._parse_js_object_literal(text)

        if not outer.get("success", False):
            # 有些情況 success 也可能是字串 "true" / "false"
            # 這裡保守處理
            if str(outer.get("success")).lower() not in ("true", "1"):
                raise ValueError(f"KTJ response success=false: {outer}")

        msg = outer.get("msg")
        if not msg:
            raise ValueError("KTJ response missing 'msg'")

        inner = json.loads(msg)  # msg 是 JSON 字串
        return inner

    @staticmethod
    def _parse_js_object_literal(s: str) -> dict:
        s = s.strip()

        # 去掉最外層 ()（如果有）
        if s.startswith("(") and s.endswith(")"):
            s = s[1:-1].strip()

        # 將未加引號的 key 變成 "key":
        s = re.sub(r'([{,]\s*)([A-Za-z_]\w*)(\s*:)', r'\1"\2"\3', s)

        return json.loads(s)


class KtjTrackingInfoAdapter(TrackingInfoAdapter):
    @staticmethod
    def convert(raw_data: dict) -> TrackingInfo | None:
        results = raw_data.get("result") or []
        if not results:
            return None

        item = results[0] or {}
        course = item.get("course") or []
        if not course:
            return None

        # 你貼的回傳第一筆是最新狀態（如果未來遇到相反，可在這裡反轉）
        latest = course[0]

        order_id = item.get("bolNo") or latest.get("bolNo")

        # 時間：優先用 processCargoCrtDAteAndTime（注意原始 key 大小寫就是這樣）
        time_str = latest.get("processCargoCrtDAteAndTime")
        if not time_str:
            d = latest.get("processCargoCrtDate")  # YYYY-MM-DD
            t = latest.get("processCargoCrtTime")  # HH:MM:SS
            if d and t:
                time_str = f"{d}T{t}"

        status_message = (latest.get("statusIdName") or "").strip()

        # 大榮常見「已送達/完成」字眼，你可依實際再增減
        delivered_keywords = ["簽收", "配達", "已送達", "已完成配送", "已完成", "配送完成"]
        is_delivered = any(k in status_message for k in delivered_keywords)

        return TrackingInfo(
            order_id=order_id,
            platform=Platform.Ktj.value,  # enums 裡要有 KTJ
            status=status_message,
            time=_normalize_time(time_str),
            is_delivered=is_delivered,
            raw_data=raw_data,
        )


def _normalize_time(s: str | None) -> str | None:
    """輸出成 'YYYY/MM/DD HH:MM'，例如 2025/12/16 09:14"""
    if not s:
        return None

    s = s.strip()

    # 統一分隔符號
    s = s.replace(" ", "T")

    # 去掉毫秒（如果有）
    # e.g. 2025-12-16T05:08:33.000 -> 2025-12-16T05:08:33
    s = re.sub(r"\.\d+$", "", s)

    # 允許缺秒：2025-12-16T05:08 -> 補 :00
    if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$", s):
        s += ":00"

    # 解析
    try:
        dt = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        # 如果格式真的不符合，就原樣回傳（避免整個 tracking 壞掉）
        return s

    return dt.strftime("%Y/%m/%d %H:%M")
