from .base import Tracker, TrackingInfo
from .enums import Platform
from .okmart import OKMartTracker
from .seven_eleven import SevenElevenTracker


class TrackerFactory:
    @staticmethod
    def create(platform: Platform) -> Tracker:
        match platform:
            case Platform.SevenEleven:
                return SevenElevenTracker()
            case Platform.OKMart:
                return OKMartTracker()
            case _:
                raise ValueError(f"Invalid platform: {platform}")


def track(platform: Platform, order_id: str) -> TrackingInfo | None:
    tracker = TrackerFactory.create(platform)
    return tracker.search(order_id)
