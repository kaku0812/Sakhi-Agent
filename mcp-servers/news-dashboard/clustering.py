import os
import sys
from typing import List
from collections import defaultdict

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from models import Article, NewsCluster


class ArticleClusterer:
    """Clusters articles by location and category."""
    
    def cluster_articles(self, articles: List[Article]) -> List[NewsCluster]:
        """Cluster articles by location and category."""
        clusters = defaultdict(list)
        
        for article in articles:
            if not article.category:
                continue
                
            key = (article.location or "Unknown", article.category)
            clusters[key].append(article)
        
        results = []
        for (location, category), items in clusters.items():
            cluster = NewsCluster(
                cluster_title=f"{category.replace('_', ' ').title()} in {location}",
                location=location,
                category=category,
                incident_count=len(items),
                articles=items
            )
            results.append(cluster)
        
        return results
