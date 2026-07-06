import asyncio

import pytest

from parcel_tw import Platform, track, track_async


@pytest.mark.parametrize("platform", list(Platform))
@pytest.mark.parametrize("order_id", [None, "", "   ", "AB 123", "AB/123", "A"])
def test_invalid_order_id_returns_none_without_external_lookup(platform, order_id):
    assert track(order_id, platform) is None
    assert asyncio.run(track_async(order_id, platform)) is None


def test_seven_eleven_keeps_platform_specific_length_validation():
    assert track("1234567890", Platform.SevenEleven) is None
    assert asyncio.run(track_async("1234567890", Platform.SevenEleven)) is None


@pytest.mark.parametrize("platform", [Platform.EzShip, Platform.HiLife])
def test_ezship_backed_platforms_reject_values_over_form_limit(platform):
    assert track("123456789012", platform) is None
    assert asyncio.run(track_async("123456789012", platform)) is None
