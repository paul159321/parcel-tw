import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

ORDER_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{1,63}$")


def normalize_order_id(order_id: str) -> str | None:
    if not isinstance(order_id, str):
        return None

    value = order_id.strip()
    if not value or not ORDER_ID_PATTERN.fullmatch(value):
        return None
    return value


class ParcelTrackingError(Exception):
    """Base exception for parcel-tw package."""
    pass


class NetworkError(ParcelTrackingError):
    """Network or HTTP request failed."""
    pass


class CaptchaError(ParcelTrackingError):
    """Failed to solve captcha or retry limit reached."""
    pass


@dataclass
class TrackingInfo:
    order_id: str
    platform: str
    status: str
    time: str | None
    is_delivered: bool
    raw_data: Any = field(repr=False)


class Tracker(ABC):
    def normalize_order_id(self, order_id: str) -> str | None:
        return normalize_order_id(order_id)

    @abstractmethod
    def track_status(self, order_id: str) -> TrackingInfo | None:
        """
        Track the parcel status by order_id

        Parameters
        ----------
        order_id : str
            The order_id of the parcel

        Returns
        -------
        TrackingInfo | None
            A `TrackingInfo` object with the status details of the parcel,
            or `None` if no information is available.
        """
        pass

    @abstractmethod
    async def track_status_async(self, order_id: str) -> TrackingInfo | None:
        """
        Track the parcel status by order_id asynchronously

        Parameters
        ----------
        order_id : str
            The order_id of the parcel

        Returns
        -------
        TrackingInfo | None
            A `TrackingInfo` object with the status details of the parcel,
            or `None` if no information is available.
        """
        pass


class RequestHandler(ABC):
    @abstractmethod
    def get_data(self, order_id: str) -> Any:
        """
        Get tracking info from the platform API

        Parameters
        ----------
        order_id: str
            The order ID of the parcel

        Returns
        -------
        Any
            The tracking information of the parcel
        """
        pass

    @abstractmethod
    async def get_data_async(self, order_id: str) -> Any:
        """
        Get tracking info from the platform API asynchronously

        Parameters
        ----------
        order_id: str
            The order ID of the parcel

        Returns
        -------
        Any
            The tracking information of the parcel
        """
        pass


class TrackingInfoAdapter(ABC):
    @staticmethod
    @abstractmethod
    def convert(raw_data: Any, order_id: str | None = None) -> TrackingInfo | None:
        """
        Convert the raw data to `TrackingInfo` object

        Parameters
        ----------
        raw_data : Any
            The raw data from the platform API
        order_id : str | None
            The optional order ID if it's not present in raw_data

        Returns
        -------
        TrackingInfo | None
            A `TrackingInfo` object with the status details of the parcel,
            or `None` if no information is available.
        """
        pass
