import asyncio
import os

import pytest

from parcel_tw import Platform, track, track_async


BIAN_LI_DAI_ORDER_ID = os.getenv("BIAN_LI_DAI_ORDER_ID")


def require_order_id() -> str:
    if not BIAN_LI_DAI_ORDER_ID:
        pytest.skip("set BIAN_LI_DAI_ORDER_ID to run live 台灣便利帶 tests")
    return BIAN_LI_DAI_ORDER_ID


@pytest.mark.live
def test_bian_li_dai_live():
    result = track(require_order_id(), Platform.BianLiDai)
    assert result is not None
    assert result.platform == Platform.BianLiDai.value


@pytest.mark.live
def test_bian_li_dai_live_async():
    result = asyncio.run(track_async(require_order_id(), Platform.BianLiDai))
    assert result is not None
    assert result.platform == Platform.BianLiDai.value
