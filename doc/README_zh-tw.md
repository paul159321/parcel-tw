# parcel-tw

<p align="center">
    <img src="https://raw.githubusercontent.com/ryanycs/parcel-tw/main/img/box.png" width=100><br>
    <a href="https://www.flaticon.com/free-icons/box" title="box icons">Box icons created by Good Ware - Flaticon</a>
</p>

<p align="center">
    <img src="https://img.shields.io/github/license/ryanycs/parcel-tw" alt=""><br>
    <a href="../README.md">English</a> <b>繁體中文</b>
</p>

## 關於

`parcel_tw` 是用來查詢台灣物流狀態的 Python 套件，提供同步與非同步兩種一致的查詢介面。

## 支援平台

| Platform enum | 物流平台 |
| --- | --- |
| `Platform.SevenEleven` | 7-11 e-tracking |
| `Platform.FamilyMart` | 全家 |
| `Platform.HiLife` | 萊爾富，透過 ezShip 查詢 |
| `Platform.OKMart` | OK Mart |
| `Platform.Shopee` | 蝦皮店到店 / Shopee Xpress |
| `Platform.Hct` | 新竹物流 |
| `Platform.Tcat` | 黑貓宅急便 |
| `Platform.Ecan` | 宅配通 |
| `Platform.Ktj` | 嘉里大榮 |
| `Platform.Pst` | 中華郵政 |
| `Platform.EzShip` | ezShip 台灣便利配 |
| `Platform.BianLiDai` | 台灣便利帶 |

## 安裝

### 需求

- Python 3.10+
- 可連線到目標物流商查詢系統

7-11 與新竹物流查詢流程需要驗證碼辨識；目前實作使用 Python 套件 `ddddocr`。

### 透過 pip 安裝

```bash
pip install parcel-tw
```

### 本機開發安裝

```bash
pip install -e ".[test]"
```

## 使用方式

### 同步查詢

```python
from parcel_tw import Platform, ParcelTrackingError, track

order_id = "order_id here"

try:
    result = track(order_id, Platform.SevenEleven)
    if result:
        print(f"狀態: {result.status}")
    else:
        print("查無包裹資料")
except ParcelTrackingError as e:
    print(f"查詢失敗: {e}")
```

### 非同步查詢

```python
import asyncio

from parcel_tw import Platform, ParcelTrackingError, track_async


async def main():
    order_id = "order_id here"

    try:
        result = await track_async(order_id, Platform.SevenEleven)
        if result:
            print(f"狀態: {result.status}")
        else:
            print("查無包裹資料")
    except ParcelTrackingError as e:
        print(f"查詢失敗: {e}")


asyncio.run(main())
```

`track()` 與 `track_async()` 查到資料時會回傳 `TrackingInfo`。

```python
result = track(order_id, Platform.SevenEleven)

print(result.order_id)       # 單號
print(result.platform)       # 物流平台
print(result.status)         # 包裹狀態
print(result.time)           # 更新時間
print(result.is_delivered)   # 是否已送達
print(result.raw_data)       # 解析後的物流原始資料
```

空白、含空白或特殊符號等明顯無效的單號會在本地直接回傳 `None`，不會送出外部查詢。物流商回覆查無資料時也會轉成 `None`。

## 測試

一般單元測試不需要連線：

```bash
pytest
```

Live integration tests 會呼叫真實物流商服務，需在 `.env` 放入測試單號：

```env
SEVEN_ELEVEN_ORDER_ID=
OKMART_ORDER_ID=
FAMILY_MART_ORDER_ID=
SHOPEE_ORDER_ID=
HILIFE_ORDER_ID=
EZSHIP_ORDER_ID=
BIAN_LI_DAI_ORDER_ID=
```

明確執行 live 測試：

```bash
pytest -m live --run-live
```

## 發版提醒

`dist/` 已被 `.gitignore` 排除。建立新版發行包前，請先清空 `dist/` 裡的舊 wheel 和 source archive，再從目前原始碼重新 build，避免誤上傳舊版檔案。

## 授權

Distributed under the MIT License. See `LICENSE` for more information.
