import json
import ssl

import requests

url_InquiryOrders = "https://ecfme.fme.com.tw/FMEDCFPWebV2_II/list.aspx/InquiryOrders"
url_GetOrderDetail = "https://ecfme.fme.com.tw/FMEDCFPWebV2_II/list.aspx/GetOrderDetail"


class TLSAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        ctx.options |= 0x4  # <-- the key part here, OP_LEGACY_SERVER_CONNECT
        kwargs["ssl_context"] = ctx
        return super(TLSAdapter, self).init_poolmanager(*args, **kwargs)


def getRequestsSession():
    s = requests.Session()
    s.mount("https://", TLSAdapter())
    return s


def familyMart(*order_no):
    headers = {"Content-Type": "application/json; charset=UTF-8"}
    payload = {"ListEC_ORDER_NO": ",".join(order_no)}

    sess = getRequestsSession()
    resp = sess.post(url_InquiryOrders, json=payload, headers=headers)
    s = resp.text.replace("\\", "")
    json_data = json.loads(s[6:-2])
    print(json.dumps(json_data, indent=4, ensure_ascii=False))
    return json_data
    for i in json_data["List"]:
        pass
        print(i["EC_ORDER_NO"], i["ORDERMESSAGE"])

    for order in json_data["List"]:
        payload = {
            "EC_ORDER_NO": order["EC_ORDER_NO"],
            "ORDER_NO": order["ORDER_NO"],
            "RCV_USER_NAME": None,
        }
        resp = sess.post(url_GetOrderDetail, json=payload, headers=headers)
        s = resp.text.replace("\\", "")
        print(json.dumps(json.loads("{" + s[7:-3] + "}"), indent=4, ensure_ascii=False))


if __name__ == "__main__":
    familyMart("03730824520", "315767994")
