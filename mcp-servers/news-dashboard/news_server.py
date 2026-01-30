#!/usr/bin/env python3

import os
import sys
import logging
from typing import Dict, Any

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from mcp.server.fastmcp import FastMCP
from sources import IndianNewsSources
from fetcher import ArticleFetcher
from processor import ArticleProcessor
from clustering import ArticleClusterer


class WomenSafetyNewsMCP:
    """MCP Server for women safety news dashboard."""
    
    def __init__(self):
        self.sources = IndianNewsSources()
        self.fetcher = ArticleFetcher()
        self.processor = ArticleProcessor()
        self.clusterer = ArticleClusterer()
        self.mcp = FastMCP("hackathon-women-safety-news")
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._register_tools()
    
    def _register_tools(self):
        """Register MCP tools."""
        
        @self.mcp.tool()
        def hackathon_women_safety_news_dashboard(location: str = None) -> Dict[str, Any]:
            """
            Generate a clustered women safety news dashboard with links.
            Fetches RSS feeds, filters women safety incidents, clusters by location
            
            Args:
                location: Optional location to filter articles (e.g., "delhi", "mumbai", "bangalore")
            """
            try:
                self.logger.info(f"Generating news dashboard for location: {location}")
                
                # Fetch articles
                rss_sources = self.sources.get_sources()
                raw_articles = self.fetcher.fetch_all(rss_sources)
                
                # Process articles
                processed_articles = []
                for article in raw_articles:
                    if self.processor.is_safety_related(article):
                        processed_article = self.processor.extract_location(article, location)
                        if processed_article:
                            processed_article.category = self.processor.determine_category(processed_article)
                            processed_articles.append(processed_article)
                
                if not processed_articles:
                    return {
                        "message": "No relevant articles found",
                        "clusters": []
                    }
                
                # Cluster articles
                clusters = self.clusterer.cluster_articles(processed_articles)
                
                # Convert to dict format for JSON serialization
                cluster_dicts = []
                for cluster in clusters:
                    article_dicts = []
                    for article in cluster.articles:
                        article_dicts.append({
                            "title": article.title,
                            "summary": article.summary,
                            "url": article.url,
                            "source": article.source,
                            "published": article.published
                        })
                    
                    cluster_dicts.append({
                        "cluster_title": cluster.cluster_title,
                        "location": cluster.location,
                        "category": cluster.category,
                        "incident_count": cluster.incident_count,
                        "articles": article_dicts
                    })
                
                return {
                    "message": f"Found {len(processed_articles)} articles in {len(clusters)} clusters",
                    "clusters": cluster_dicts
                }
                
            except Exception as e:
                self.logger.error(f"Error generating news dashboard: {str(e)}")
                return {
                    "message": f"Error generating news dashboard: {str(e)}",
                    "error": str(e),
                    "clusters": []
                }
    
    def run(self):
        """Start the MCP server."""
        self.logger.info("Starting Women Safety News MCP Server...")
        self.mcp.run(transport="stdio")


def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )


def main():
    """Main entry point."""
    try:
        setup_logging()
        server = WomenSafetyNewsMCP()
        server.run()
        
    except Exception as e:
        logging.error(f"Failed to start news server: {str(e)}")
        raise


if __name__ == "__main__":
    main()
