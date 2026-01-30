import os
import sys
import logging
from typing import Optional

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from models import Article


class ArticleProcessor:
    """Processes and filters articles for women safety content."""
    
    SAFETY_KEYWORDS = [
        "rape", "sexual", "harassment", "molestation",
        "woman", "women", "girl", "assault", "stalking",
        "abuse", "violence", "attack", "molest"
    ]
    
    CATEGORY_KEYWORDS = {
        "sexual_harassment": ["harassment", "molest", "grope", "inappropriate"],
        "rape": ["rape", "sexual assault", "gang rape"],
        "stalking": ["stalk", "follow", "chase"],
        "domestic_violence": ["domestic", "husband", "family", "home"],
        "assault": ["assault", "attack", "beat", "violence"],
        "abuse": ["abuse", "torture", "cruelty"]
    }
    
    INDIAN_CITIES = [
        "delhi", "mumbai", "bangalore", "chennai", "kolkata",
        "hyderabad", "pune", "ahmedabad", "jaipur", "lucknow",
        "south delhi", "north delhi", "dwarka", "rohini"
    ]
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def is_safety_related(self, article: Article) -> bool:
        """Check if article is related to women safety."""
        text = (article.title + article.summary).lower()
        return any(keyword in text for keyword in self.SAFETY_KEYWORDS)
    
    def extract_location(self, article: Article, user_location: Optional[str] = None) -> Optional[Article]:
        """Extract location from article."""
        text = (article.title + article.summary).lower()
        
        # If user specified location, only return matching articles
        if user_location:
            if user_location.lower() in text:
                article.location = user_location.title()
                return article
            return None
        
        # Auto-detect location
        for city in self.INDIAN_CITIES:
            if city in text:
                article.location = city.title()
                return article
        
        article.location = "Unknown"
        return article
    
    def determine_category(self, article: Article) -> str:
        """Determine article category based on content."""
        text = (article.title + article.summary).lower()
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return "women_safety_incident"
