import requests
from flask import current_app
from datetime import datetime, timedelta
import time
import json

class TMDbClient:
    def __init__(self):
        self.base_url = None
        self.api_key = None
        self.image_base_url = None
        self.config_cached_at = None
        self.session = requests.Session()
        self.session.timeout = 10
    
    def _ensure_config(self):
        """Ensure we have the configuration from the current app context"""
        if self.base_url is None and current_app:
            self.base_url = current_app.config['TMDB_BASE_URL']
            self.api_key = current_app.config['TMDB_API_KEY']
        
    def _make_request(self, endpoint, params=None, retries=3):
        """Make API request with retry logic and rate limiting"""
        self._ensure_config()
        
        if params is None:
            params = {}
        
        params['api_key'] = self.api_key
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        for attempt in range(retries):
            try:
                response = self.session.get(url, params=params)
                
                if response.status_code == 429:
                    # Rate limited - wait and retry
                    retry_after = int(response.headers.get('Retry-After', 1))
                    time.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt == retries - 1:
                    current_app.logger.error(f"TMDb API request failed: {e}")
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def get_configuration(self):
        """Get TMDb configuration, cached for 24 hours"""
        if (self.image_base_url is None or 
            self.config_cached_at is None or 
            datetime.utcnow() - self.config_cached_at > timedelta(hours=24)):
            
            try:
                config = self._make_request('/configuration')
                if config:
                    self.image_base_url = config['images']['secure_base_url']
                    self.config_cached_at = datetime.utcnow()
            except Exception as e:
                current_app.logger.error(f"Failed to fetch TMDb configuration: {e}")
                # Fallback to default
                self.image_base_url = 'https://image.tmdb.org/t/p/'
        
        return self.image_base_url
    
    def search_movies(self, query, page=1):
        """Search for movies"""
        try:
            return self._make_request('/search/movie', {
                'query': query,
                'page': page
            })
        except Exception as e:
            current_app.logger.error(f"Movie search failed: {e}")
            return None
    
    def search_tv(self, query, page=1):
        """Search for TV shows"""
        try:
            return self._make_request('/search/tv', {
                'query': query,
                'page': page
            })
        except Exception as e:
            current_app.logger.error(f"TV search failed: {e}")
            return None
    
    def search_multi(self, query, page=1):
        """Search both movies and TV shows"""
        try:
            return self._make_request('/search/multi', {
                'query': query,
                'page': page
            })
        except Exception as e:
            current_app.logger.error(f"Multi search failed: {e}")
            return None
    
    def get_movie_details(self, movie_id, append_to_response='credits'):
        """Get movie details"""
        try:
            params = {}
            if append_to_response:
                params['append_to_response'] = append_to_response
            return self._make_request(f'/movie/{movie_id}', params)
        except Exception as e:
            current_app.logger.error(f"Failed to get movie details: {e}")
            return None
    
    def get_tv_details(self, tv_id, append_to_response='credits'):
        """Get TV show details"""
        try:
            params = {}
            if append_to_response:
                params['append_to_response'] = append_to_response
            return self._make_request(f'/tv/{tv_id}', params)
        except Exception as e:
            current_app.logger.error(f"Failed to get TV details: {e}")
            return None
    
    def build_image_url(self, path, size='w500'):
        """Build full image URL"""
        if not path:
            return None
        
        base_url = self.get_configuration()
        return f"{base_url}{size}{path}"

# Global client instance
tmdb_client = TMDbClient()