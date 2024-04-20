import os
import sys

import pytest

src_dir = os.path.join(os.path.dirname(__file__), "../src")
sys.path.insert(0, src_dir)
print(sys.path)


def test_etracking():
    from package_tracking.etracking import etracking

    res = etracking("87717609642")
    assert res["msg"] == "success"

    res = etracking("87717609641567")
    assert res["msg"] == "查無該取貨/繳費編號資料，請重新輸入。"
