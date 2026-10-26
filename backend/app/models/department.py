import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def slugify_name(name: str) -> str:
    """Generate a clean, URL-safe slug from a department name."""
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower())
    return cleaned.strip("-")


@dataclass
class Department:
    name: str
    code: str
    slug: Optional[str] = None
    description: Optional[str] = None
    avg_consultation_time: int = 15
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        slug = self.slug or slugify_name(self.name)
        return {
            "name": self.name.strip(),
            "code": self.code.upper().strip(),
            "slug": slug,
            "description": self.description,
            "avg_consultation_time": self.avg_consultation_time,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
