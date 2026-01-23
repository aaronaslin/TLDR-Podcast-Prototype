"""Core domain models."""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class Digest:
    """Represents a fetched digest email."""
    body: str
    received_at: Optional[datetime] = None
    subject: Optional[str] = None


@dataclass
class Episode:
    """Represents a podcast episode entry."""
    title: str
    audio_url: str
    description: str
    pub_date: datetime
    file_size: int
    link: str

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["pub_date"] = self.pub_date.isoformat()
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Episode":
        return Episode(
            title=data["title"],
            audio_url=data["audio_url"],
            description=data["description"],
            pub_date=datetime.fromisoformat(data["pub_date"]),
            file_size=int(data["file_size"]),
            link=data["link"],
        )
