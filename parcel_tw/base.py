import requests
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class TrackingInfo:
    order_id: str
    platform: str
    status: str
    time: str | None
    is_delivered: bool
    raw_data: dict = field(repr=False)


class Tracker(ABC):
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


class RequestHandler(ABC):
    def __init__(self):
        self.session = requests.Session()

    @abstractmethod
    def get_data(self, order_id: str) -> dict:
        """
        Get tracking info from the platform API

        Parameters
        ----------
        order_id: str
            The order ID of the parcel

        Returns
        -------
        dict
            The tracking information of the parcel in `dict`, or `None` if failed
        """
        pass


class TrackingInfoAdapter(ABC):
    @staticmethod
    @abstractmethod
    def convert(raw_data: dict | None) -> TrackingInfo | None:
        """
        Convert the raw data to `TrackingInfo` object

        Parameters
        ----------
        raw_data : dict | None
            The raw data from the platform API

        Returns
        -------
        TrackingInfo | None
            A `TrackingInfo` object with the status details of the parcel,
            or `None` if no information is available.
        """
        pass
