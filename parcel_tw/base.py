from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TrackingInfo:
    order_id: str
    platform: str
    status: str
    time: str | None
    is_delivered: bool
    raw_data: dict


class Tracker(ABC):
    @abstractmethod
    def search(self, order_id: str) -> TrackingInfo | None:
        pass
