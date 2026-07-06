from .base import Tracker, TrackingInfo
from .enums import Platform
from .family_mart import FamilyMartTracker
from .okmart import OKMartTracker
from .seven_eleven import SevenElevenTracker
from .shopee import ShopeeTracker
from .hct import HctTracker
from .tcat import TcatTracker
from .ecan import EcanTracker
from .ktj import KtjTracker
from .pst import PstTracker
from .ezship import EzShipTracker, HiLifeTracker


class TrackerFactory:
    @staticmethod
    def create_tracker(platform: Platform) -> Tracker:
        """
        Create a tracker based on the platform

        Parameters
        ----------
        platform : Platform
            The platform of the parcel

        Returns
        -------
        Tracker
            A tracker object for the specified platform

        Raises
        ------
        ValueError
            If the platform is not supported
        """

        match platform:
            case Platform.SevenEleven:
                return SevenElevenTracker()
            case Platform.FamilyMart:
                return FamilyMartTracker()
            case Platform.HiLife:
                return HiLifeTracker()
            case Platform.OKMart:
                return OKMartTracker()
            case Platform.Shopee:
                return ShopeeTracker()
            case Platform.Hct:
                return HctTracker()
            case Platform.Tcat:
                return TcatTracker()
            case Platform.Ecan:
                return EcanTracker()
            case Platform.Ktj:
                return KtjTracker()
            case Platform.Pst:
                return PstTracker()
            case Platform.EzShip:
                return EzShipTracker()
            case _:
                raise ValueError(f"Invalid platform: {platform}")


def track(order_id: str, platform: Platform) -> TrackingInfo | None:
    """
    Track the parcel status by order_id

    Parameters
    ----------
    order_id : str
        The order_id of the parcel
    platform : Platform
        The platform of the parcel

    Returns
    -------
    TrackingInfo | None
        A `TrackingInfo` object with the status details of the parcel,
        or `None` if no information is available.
    """

    tracker = TrackerFactory.create_tracker(platform)
    normalized_order_id = tracker.normalize_order_id(order_id)
    if normalized_order_id is None:
        return None
    return tracker.track_status(normalized_order_id)


async def track_async(order_id: str, platform: Platform) -> TrackingInfo | None:
    """
    Track the parcel status by order_id asynchronously

    Parameters
    ----------
    order_id : str
        The order_id of the parcel
    platform : Platform
        The platform of the parcel

    Returns
    -------
    TrackingInfo | None
        A `TrackingInfo` object with the status details of the parcel,
        or `None` if no information is available.
    """

    tracker = TrackerFactory.create_tracker(platform)
    normalized_order_id = tracker.normalize_order_id(order_id)
    if normalized_order_id is None:
        return None
    return await tracker.track_status_async(normalized_order_id)
