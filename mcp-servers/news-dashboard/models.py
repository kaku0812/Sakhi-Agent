from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Article:
    """Data class for news articles."""
    title: str
    summary: str
    published: str
    url: str
    source: str
    location: Optional[str] = None
    category: Optional[str] = None


@dataclass
class NewsCluster:
    """Data class for clustered news articles."""
    cluster_title: str
    location: str
    category: str
    incident_count: int
    articles: List[Article]
