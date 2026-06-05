# parcel-tw

<p align="center">
    <img src="https://raw.githubusercontent.com/ryanycs/parcel-tw/main/img/box.png" width=100><br>
    <a href="https://www.flaticon.com/free-icons/box" title="box icons">Box icons created by Good Ware - Flaticon</a>
</p>

<p align="center">
    <img src="https://img.shields.io/github/license/ryanycs/parcel-tw" alt=""><br>
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

### Install via pip

```bash
$ pip install parcel-tw
```

## Usage

### 同步使用方式

```python
from parcel_tw import track, Platform, ParcelTrackingError

order_id = "order_id here"
try:
    result = track(order_id, Platform.SevenEleven) # 查詢 7-11 包裹
    if result:
        print(f"包裹狀態: {result.status}")
    else:
        print("查無此包裹。")
except ParcelTrackingError as e:
    print(f"查詢失敗: {e}")
```

### 非同步使用方式

```python
import asyncio
from parcel_tw import track_async, Platform, ParcelTrackingError

async def main():
    order_id = "order_id here"
    try:
        result = await track_async(order_id, Platform.SevenEleven)
        if result:
            print(f"包裹狀態: {result.status}")
        else:
            print("查無此包裹。")
    except ParcelTrackingError as e:
        print(f"查詢失敗: {e}")

asyncio.run(main())
```

`track()` / `track_async()` 會回傳一個 `TrackingInfo` 物件，可以取得包裹的狀態。

```python
result = track(order_id, Platform.SevenEleven)

print(result.order_id) # 取貨編號
print(result.platform) # 物流平台
print(result.status) # 包裹狀態
print(result.time) # 更新時間
print(result.is_delivered) # 是否已送達
print(result.raw_data) # 爬蟲分析後的包裹詳細資料 (dict/list)
```

## Roadmap

- [x] 7-11
- [x] 全家
- [ ] 萊爾富
- [x] OK Mart
- [x] 蝦皮店到店
- [ ] 中華郵政
- [x] 上架到 PyPI
- [x] asyncio 異步爬蟲

## License

Distributed under the MIT License. See `LICENSE` for more information.
