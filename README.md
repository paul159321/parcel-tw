# parcel-tw

<p align="center">
    <img src="img/box.png" width=100><br>
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
track(Platform.SevenEleven, order_id) # track 7-11 package
track(Platform.FamilyMart, order_id) # track FamilyMart package
track(Platform.OKMart, order_id) # track OK Mart package
track(Platform.Shopee, order_id) # track Shopee package
```

`track()` will return a `TrackingInfo` object, which contains the status of the package.

```python
result = track(Platform.SevenEleven, order_id)

print(result.order_id) # order id
print(result.platform) # logistics platform
print(result.status) # package status
print(result.time) # update time
print(result.is_delivered) # is delivered
print(result.raw_data) # Package details after crawler analysis (dict)
```

## Roadmap

- [x] 7-11
- [x] FamilyMart
- [ ] Hi-Life
- [x] OK Mart
- [x] Shopee
- [ ] Chunghwa Post
- [ ] Upload to PyPI
- [ ] asyncio crawler

## License

Distributed under the MIT License. See `LICENSE` for more information.
