# parcel-tw

<p align="center">
    <img src="../img/box.png" width=100><br>
    <a href="https://www.flaticon.com/free-icons/box" title="box icons">Box icons created by Good Ware - Flaticon</a>
</p>

<p align="center">
    <img href="https://img.shields.io/github/license/ryanycs/parcel-tw" alt=""><br>
    <a href="../README.md">English</a> <b>繁體中文</b>
</p>


## About

parcel_tw 是一個查詢台灣包裹進度的 Python package，支援多家的物流系統(7-11、全家、OK、蝦皮店到店)。

## Installation

### Requirements

- Python 3.10+
- tesseract-ocr

因為 7-11 的 E-Tracking 貨態查詢系統無法繞過 Captcha 檢測，所以需要使用 OCR 來解析驗證碼。

```sudo apt install tesseract-ocr```

### Install package manually

```bash
git clone https://github.com/ryanycs/parcel-tw.git
cd parcel-tw
pip install .
```

## Usage

```python
from parcel_tw import track, Platform

order_id = "order_id here"
track(Platform.SevenEleven, order_id) # 查詢 7-11 包裹
track(Platform.FamilyMart, order_id) # 查詢全家包裹
track(Platform.OKMart, order_id) # 查詢 OK Mart 包裹
track(Platform.Shopee, order_id) # 查詢蝦皮店到店包裹
```

`track()` 會返回一個 `TrackingInfo` 物件，可以取得包裹的狀態。

```python
result = track(Platform.SevenEleven, order_id)

print(result.order_id) # 取貨編號
print(result.platform) # 物流平台
print(result.status) # 包裹狀態
print(result.time) # 更新時間
print(result.is_delivered) # 是否已送達
print(result.raw_data) # 爬蟲分析後的包裹詳細資料 (dict)
```

## Roadmap

- [x] 7-11
- [x] 全家
- [ ] 萊爾富
- [x] OK Mart
- [x] 蝦皮店到店
- [ ] 中華郵政
- [ ] 上架到 PyPI
- [ ] asyncio 異步爬蟲

## License

Distributed under the MIT License. See `LICENSE` for more information.
