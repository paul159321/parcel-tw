from parcel_tw.enums import Platform
from parcel_tw.ecan import EcanTrackingInfoAdapter
from parcel_tw.ezship import EzShipTrackingInfoAdapter, HiLifeTrackingInfoAdapter
from parcel_tw.family_mart import FamilyMartTrackingInfoAdapter
from parcel_tw.hct import HctTrackingInfoAdapter
from parcel_tw.ktj import KtjTrackingInfoAdapter
from parcel_tw.okmart import OKMartResponseParser, OKMartTrackingInfoAdapter
from parcel_tw.pst import PstTrackingInfoAdapter
from parcel_tw.seven_eleven import SevenElevenResponseParser, SevenElevenTrackingInfoAdapter
from parcel_tw.shopee import ShopeeTrackingInfoAdapter
from parcel_tw.tcat import TcatTrackingInfoAdapter


def test_seven_eleven_parser_and_adapter_convert_tracking_info():
    html = """
    <html>
      <body>
        <div class="m_news">包裹配達取件門市2026/07/06 12:34:56</div>
        <div class="info">
          <h4 id="servicetype">交貨便</h4>
          <span id="query_no">711ABC12</span>
        </div>
        <div class="shipping"><p>包裹已送達門市</p></div>
      </body>
    </html>
    """

    raw = SevenElevenResponseParser(html).parse()
    info = SevenElevenTrackingInfoAdapter.convert(raw)

    assert info is not None
    assert info.order_id == "711ABC12"
    assert info.platform == Platform.SevenEleven.value
    assert info.status == "包裹配達取件門市"
    assert info.time == "2026/07/06 12:34:56"
    assert info.is_delivered is True


def test_family_mart_adapter_converts_latest_status():
    raw = {
        "List": [
            {
                "ORDER_NO": "FM123456789",
                "ORDER_DATE_R": "2026/07/06 12:34",
                "STATUS_D": "已完成取件",
            }
        ]
    }

    info = FamilyMartTrackingInfoAdapter.convert(raw)

    assert info is not None
    assert info.order_id == "FM123456789"
    assert info.platform == Platform.FamilyMart.value
    assert info.time == "2026/07/06 12:34:00"
    assert info.status == "已完成取件"
    assert info.is_delivered is True


def test_okmart_parser_and_adapter_convert_tracking_info():
    html = """
    <html>
      <body>
        <div class="triNo">TRI123</div>
        <div class="odNo">OK123456789</div>
        <div class="type">店到店</div>
        <div class="status">已取貨</div>
        <div class="stNo">001</div>
        <div class="stNm">寄件門市</div>
        <div class="stNm">取件門市</div>
        <div class="takeFrom">2026/07/06 10:00</div>
        <div class="takeTo">2026/07/06 20:00</div>
        <div class="takeAt">2026/07/06 13:00</div>
        <div class="taker">王小明</div>
      </body>
    </html>
    """

    raw = OKMartResponseParser(html).parse()
    info = OKMartTrackingInfoAdapter.convert(raw)

    assert info is not None
    assert info.order_id == "OK123456789"
    assert info.platform == Platform.OKMart.value
    assert info.status == "已取貨"
    assert info.time == "2026/07/06 10:00"
    assert info.is_delivered is True


def test_shopee_adapter_converts_tracking_api_response():
    raw = {
        "data": {
            "sls_tracking_number": "SPXTW123456789",
            "tracking_list": [
                {
                    "message": "Parcel collected",
                    "timestamp": 1783334400,
                    "status": "SP_Collection_Collected",
                }
            ],
        }
    }

    info = ShopeeTrackingInfoAdapter.convert(raw)

    assert info is not None
    assert info.order_id == "SPXTW123456789"
    assert info.platform == Platform.Shopee.value
    assert info.status == "Parcel collected"
    assert info.is_delivered is True


def test_hct_adapter_converts_grid_rows():
    html = """
    <html>
      <body>
        <div class="grid-container">
          <div class="col_optime">2026/07/06 09:30</div>
          <div class="col_state">
            <span class="linkInv" onmouseover="showTip('送達')">已送達</span>
          </div>
          <div class="col_count">1件</div>
          <div class="col_office">台北營業所</div>
        </div>
      </body>
    </html>
    """

    info = HctTrackingInfoAdapter.convert({"html": html}, "HCT1234567")

    assert info is not None
    assert info.order_id == "HCT1234567"
    assert info.platform == Platform.Hct.value
    assert "已送達" in info.status
    assert info.time == "2026/07/06 09:30"
    assert info.is_delivered is True


def test_tcat_adapter_converts_table_rows():
    html = """
    <html>
      <body>
        <table class="tablelist">
          <tr><th>header</th></tr>
          <tr>
            <td><span class="bl12">TCAT123456</span></td>
            <td class="style1">配達完成</td>
            <td class="style1">2026/07/06 11:20</td>
            <td class="style1">台北營業所</td>
          </tr>
        </table>
      </body>
    </html>
    """

    info = TcatTrackingInfoAdapter.convert({"html": html}, "TCAT123456")

    assert info is not None
    assert info.order_id == "TCAT123456"
    assert info.platform == Platform.Tcat.value
    assert info.status == "配達完成(台北營業所)"
    assert info.time == "2026/07/06 11:20"
    assert info.is_delivered is True


def test_ecan_adapter_converts_sheet_rows():
    html = """
    <html>
      <body>
        <table class="sheetList">
          <tbody class="ListStyle01">
            <tr><td colspan="4">單號：ECAN123456-1</td></tr>
            <tr>
              <td>2026/07/06 12:00</td>
              <td>已送達</td>
              <td>貨件送達</td>
              <td>台北營業所</td>
            </tr>
          </tbody>
        </table>
      </body>
    </html>
    """

    info = EcanTrackingInfoAdapter.convert({"html": html}, "ECAN123456")

    assert info is not None
    assert info.order_id == "ECAN123456"
    assert info.platform == Platform.Ecan.value
    assert info.status == "已送達(台北營業所) - 貨件送達"
    assert info.time == "2026/07/06 12:00"
    assert info.is_delivered is True


def test_ktj_adapter_converts_course_rows():
    raw = {
        "result": [
            {
                "bolNo": "KTJ123456",
                "course": [
                    {
                        "bolNo": "KTJ123456",
                        "statusIdName": "簽收",
                        "processCargoCrtDAteAndTime": "2026-07-06T13:45:00",
                    }
                ],
            }
        ]
    }

    info = KtjTrackingInfoAdapter.convert(raw, "KTJ123456")

    assert info is not None
    assert info.order_id == "KTJ123456"
    assert info.platform == Platform.Ktj.value
    assert info.status == "簽收"
    assert info.time == "2026/07/06 13:45"
    assert info.is_delivered is True


def test_pst_adapter_converts_json_items():
    raw = [
        {
            "body": {
                "host_rs": {
                    "ITEM": [
                        {
                            "STATUS": "投遞成功",
                            "BRHNC": "台北郵局",
                            "DATIME": "2026/07/06 14:10",
                        }
                    ]
                }
            }
        }
    ]

    info = PstTrackingInfoAdapter.convert(raw, "PST123456")

    assert info is not None
    assert info.order_id == "PST123456"
    assert info.platform == Platform.Pst.value
    assert info.status == "投遞成功(台北郵局)"
    assert info.time == "2026/07/06 14:10"
    assert info.is_delivered is True


def test_ezship_adapter_converts_table_rows():
    html = """
    <html>
      <body>
        <div>查詢結果</div>
        <table>
          <tr>
            <th>寄件編號</th>
            <th>更新時間</th>
            <th>貨物狀態</th>
            <th>門市</th>
          </tr>
          <tr>
            <td>EZ123456789</td>
            <td>2026/07/06 15:20</td>
            <td>已取件</td>
            <td>萊爾富台北店</td>
          </tr>
        </table>
      </body>
    </html>
    """

    info = EzShipTrackingInfoAdapter.convert({"html": html, "order_id": "EZ123456789"})

    assert info is not None
    assert info.order_id == "EZ123456789"
    assert info.platform == Platform.EzShip.value
    assert info.status == "已取件"
    assert info.time == "2026/07/06 15:20"
    assert info.is_delivered is True


def test_hilife_adapter_uses_ezship_result_with_hilife_platform():
    html = """
    <html>
      <body>
        <table>
          <tr><th>更新時間</th><th>貨物狀態</th></tr>
          <tr><td>2026/07/06 16:00</td><td>貨件已送達門市</td></tr>
        </table>
      </body>
    </html>
    """

    info = HiLifeTrackingInfoAdapter.convert({"html": html, "order_id": "HL123456789"})

    assert info is not None
    assert info.order_id == "HL123456789"
    assert info.platform == Platform.HiLife.value
    assert info.status == "貨件已送達門市"
    assert info.time == "2026/07/06 16:00"
    assert info.is_delivered is True


def test_ezship_adapter_returns_none_for_not_found_page():
    html = """
    <div style="font-size:15px;">查詢結果</div>
    <div style="color:#CD5C5C;">查無資料，請重新輸入查詢條件。</div>
    """

    assert EzShipTrackingInfoAdapter.convert({"html": html, "order_id": "EZ123456789"}) is None
