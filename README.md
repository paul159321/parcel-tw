# parcel-tw

<p align="center">
    <img src="https://raw.githubusercontent.com/ryanycs/parcel-tw/main/img/box.png" width=100><br>
    <a href="https://www.flaticon.com/free-icons/box" title="box icons">Box icons created by Good Ware - Flaticon</a>
</p>

<p align="center">
    <img src="https://img.shields.io/github/license/ryanycs/parcel-tw" alt=""><br>
    <b>English</b> <a href="doc/README_zh-tw.md">繁體中文</a>
</p>

## About

parcel_tw is a Python package for tracking the status of packages in Taiwan. It supports many logistics systems (7-11, FamilyMart, OK, and Shopee).

## Installation

### Requirements

- Python 3.10+
- tesseract-ocr

Since the E-tracking system of 7-11 cannot bypass the Captcha detection, OCR is needed to parse the verification code.

```sudo apt install tesseract-ocr```

### Install via pip

```bash
$ pip install parcel-tw
```

## Usage

### Synchronous Usage

```python
from parcel_tw import track, Platform, ParcelTrackingError

order_id = "order_id here"
try:
    result = track(order_id, Platform.SevenEleven) # track 7-11 package
    if result:
        print(f"Status: {result.status}")
    else:
        print("Parcel not found.")
except ParcelTrackingError as e:
    print(f"Error tracking parcel: {e}")
```

### Asynchronous Usage

```python
import asyncio
from parcel_tw import track_async, Platform, ParcelTrackingError

async def main():
    order_id = "order_id here"
    try:
        result = await track_async(order_id, Platform.SevenEleven)
        if result:
            print(f"Status: {result.status}")
        else:
            print("Parcel not found.")
    except ParcelTrackingError as e:
        print(f"Error: {e}")

asyncio.run(main())
```

`track()` / `track_async()` will return a `TrackingInfo` object, which contains the status of the package.

```python
result = track(order_id, Platform.SevenEleven)

print(result.order_id) # order id
print(result.platform) # logistics platform
print(result.status) # package status
print(result.time) # update time
print(result.is_delivered) # is delivered
print(result.raw_data) # Package details after crawler analysis (dict/list)
```

## Roadmap

- [x] 7-11
- [x] FamilyMart
- [ ] Hi-Life
- [x] OK Mart
- [x] Shopee
- [ ] Chunghwa Post
- [x] Upload to PyPI
- [x] asyncio crawler

## License

Distributed under the MIT License. See `LICENSE` for more information.
