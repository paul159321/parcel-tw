# parcel-tw

<p align="center">
    <img src="https://raw.githubusercontent.com/ryanycs/parcel-tw/main/img/box.png" width=100><br>
    <a href="https://www.flaticon.com/free-icons/box" title="box icons">Box icons created by Good Ware - Flaticon</a>
</p>

<p align="center">
    <img src="https://img.shields.io/github/license/ryanycs/parcel-tw" alt=""><br>
    <b>English</b> <a href="doc/README_zh-tw.md">Traditional Chinese</a>
</p>

## About

`parcel_tw` is a Python package for tracking parcel status in Taiwan. It provides a common synchronous and asynchronous interface for multiple carrier systems.

## Supported Platforms

| Platform enum | Carrier |
| --- | --- |
| `Platform.SevenEleven` | 7-11 e-tracking |
| `Platform.FamilyMart` | FamilyMart |
| `Platform.HiLife` | Hi-Life via ezShip tracking |
| `Platform.OKMart` | OK Mart |
| `Platform.Shopee` | Shopee Xpress |
| `Platform.Hct` | HCT Logistics |
| `Platform.Tcat` | T-Cat |
| `Platform.Ecan` | Ecan |
| `Platform.Ktj` | KTJ Express |
| `Platform.Pst` | Chunghwa Post |
| `Platform.EzShip` | ezShip |

## Installation

### Requirements

- Python 3.10+
- Internet access to the target carrier tracking systems

7-11 and HCT require captcha recognition. The current implementation uses `ddddocr`, which is installed as a Python dependency.

### Install via pip

```bash
pip install parcel-tw
```

### Install for local development

```bash
pip install -e ".[test]"
```

## Usage

### Synchronous Usage

```python
from parcel_tw import Platform, ParcelTrackingError, track

order_id = "order_id here"

try:
    result = track(order_id, Platform.SevenEleven)
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

from parcel_tw import Platform, ParcelTrackingError, track_async


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

`track()` and `track_async()` return a `TrackingInfo` object when tracking data is available.

```python
result = track(order_id, Platform.SevenEleven)

print(result.order_id)       # order id
print(result.platform)       # logistics platform
print(result.status)         # package status
print(result.time)           # update time
print(result.is_delivered)   # delivered flag
print(result.raw_data)       # parsed carrier response
```

Invalid local input, such as blank values or values with unsupported characters, returns `None` before any carrier request is made. Carrier-side "not found" responses are also converted to `None`.

## Testing

Unit tests are designed to run without network access:

```bash
pytest
```

Live integration tests call real carrier services and require tracking IDs in `.env`:

```env
SEVEN_ELEVEN_ORDER_ID=
OKMART_ORDER_ID=
FAMILY_MART_ORDER_ID=
SHOPEE_ORDER_ID=
HILIFE_ORDER_ID=
EZSHIP_ORDER_ID=
```

Run them explicitly with:

```bash
pytest -m live --run-live
```

## Release Notes

Build artifacts are ignored through `.gitignore`. Before creating a new release, clean stale files under `dist/` and rebuild from the current source so old wheels or source archives are not uploaded by mistake.

## License

Distributed under the MIT License. See `LICENSE` for more information.
