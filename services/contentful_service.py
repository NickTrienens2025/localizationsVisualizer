import asyncio
import httpx
from typing import List, Dict, Any, Optional
import json
from datetime import datetime, timedelta

class ContentfulService:
    def __init__(self, space_id: str, environment_id: str, access_token: str):
        self.space_id = space_id
        self.environment_id = environment_id
        self.access_token = access_token
        self.base_url = f"https://api.contentful.com/spaces/{space_id}/environments/{environment_id}"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        self._cache = {}
        self._cache_expiry = {}

    async def _make_request(self, url: str, method: str = "GET", data: Dict = None) -> Dict:
        """Make HTTP request to Contentful API"""
        try:
            async with httpx.AsyncClient() as client:
                if method == "GET":
                    response = await client.get(url, headers=self.headers)
                elif method == "POST":
                    response = await client.post(url, headers=self.headers, json=data)
                elif method == "PUT":
                    response = await client.put(url, headers=self.headers, json=data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Get response content for error details
                response_content = response.text
                
                # Check for HTTP errors
                if response.status_code >= 400:
                    error_msg = f"HTTP {response.status_code}: {response_content}"
                    print(f"Contentful API HTTP Error: {error_msg}")
                    raise Exception(error_msg)
                
                # Parse JSON response
                try:
                    json_response = response.json()
                except json.JSONDecodeError as e:
                    error_msg = f"JSON Decode Error: {e}. Response: {response_content}"
                    print(f"Contentful API JSON Error: {error_msg}")
                    raise Exception(error_msg)
                
                # Check for Contentful API errors in response
                if "sys" in json_response and "type" in json_response["sys"] and json_response["sys"]["type"] == "Error":
                    error_msg = f"Contentful API Error: {json.dumps(json_response, indent=2)}"
                    print(f"Contentful API Error: {error_msg}")
                    raise Exception(error_msg)
                
                return json_response
                
        except httpx.RequestError as e:
            error_msg = f"Request Error: {str(e)}"
            print(f"Contentful API Request Error: {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            if "Contentful API" not in str(e):
                error_msg = f"Unexpected Error: {str(e)}"
                print(f"Contentful API Unexpected Error: {error_msg}")
                raise Exception(error_msg)
            raise

    async def get_entries(self, content_type: Optional[str] = None, limit: int = 1000) -> Dict:
        """Get entries from Contentful"""
        params = {"limit": str(limit)}
        if content_type:
            params["content_type"] = content_type
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{self.base_url}/entries?{query_string}"
        
        return await self._make_request(url)

    async def get_all_entries(self, content_type: Optional[str] = None) -> List[Dict]:
        """Get all entries with pagination"""
        all_entries = []
        skip = 0
        limit = 1000
        
        while True:
            params = {"limit": str(limit), "skip": str(skip)}
            if content_type:
                params["content_type"] = content_type
            
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            url = f"{self.base_url}/entries?{query_string}"
            
            response = await self._make_request(url)
            items = response.get("items", [])
            
            if not items:
                break
                
            all_entries.extend(items)
            
            if len(items) < limit:
                break
                
            skip += limit
        
        return all_entries

    async def get_entry(self, entry_id: str) -> Dict:
        """Get a specific entry by ID"""
        url = f"{self.base_url}/entries/{entry_id}"
        return await self._make_request(url)

    async def create_entry(self, content_type: str, entry_id: str, fields: Dict) -> Dict:
        """Create a new entry"""
        url = f"{self.base_url}/entries/{entry_id}"
        data = {
            "fields": fields
        }
        headers = self.headers.copy()
        headers["X-Contentful-Content-Type"] = content_type
        
        async with httpx.AsyncClient() as client:
            response = await client.put(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()

    async def update_entry(self, entry_id: str, version: int, fields: Dict) -> Dict:
        """Update an existing entry"""
        url = f"{self.base_url}/entries/{entry_id}"
        data = {
            "fields": fields
        }
        headers = self.headers.copy()
        headers["X-Contentful-Version"] = str(version)
        
        async with httpx.AsyncClient() as client:
            response = await client.put(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()

    async def publish_entry(self, entry_id: str, version: int) -> Dict:
        """Publish an entry"""
        url = f"{self.base_url}/entries/{entry_id}/published"
        headers = self.headers.copy()
        headers["X-Contentful-Version"] = str(version)
        
        async with httpx.AsyncClient() as client:
            response = await client.put(url, headers=headers)
            response.raise_for_status()
            return response.json()

    def _get_cache_key(self, method: str, **kwargs) -> str:
        """Generate cache key for method and parameters"""
        params = sorted(kwargs.items())
        return f"{method}:{hash(str(params))}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self._cache_expiry:
            return False
        return datetime.now() < self._cache_expiry[cache_key]

    async def get_cached_entries(self, content_type: Optional[str] = None, cache_duration: int = 300) -> List[Dict]:
        """Get entries with caching"""
        cache_key = self._get_cache_key("get_all_entries", content_type=content_type)
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        entries = await self.get_all_entries(content_type)
        
        # Cache the result
        self._cache[cache_key] = entries
        self._cache_expiry[cache_key] = datetime.now() + timedelta(seconds=cache_duration)
        
        return entries 