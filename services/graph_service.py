import httpx
from typing import List, Dict, Any, Optional
import json
from datetime import datetime, timedelta

class GraphService:
    def __init__(self, space_id: str, environment_id: str, access_token: str):
        self.space_id = space_id
        self.environment_id = environment_id
        self.access_token = access_token
        self.base_url = f"https://graphql.contentful.com/content/v1/spaces/{space_id}/environments/{environment_id}"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self._cache = {}
        self._cache_expiry = {}

    def _build_query_body(self, query: str) -> str:
        """Build GraphQL query body"""
        return json.dumps({
            "query": query.replace("\n", " "),
            "variables": {}
        })

    async def _make_graphql_request(self, query: str) -> Dict:
        """Make GraphQL request to Contentful"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers=self.headers,
                    content=self._build_query_body(query)
                )
                
                # Get response content for error details
                response_content = response.text
                
                # Check for HTTP errors
                if response.status_code >= 400:
                    error_msg = f"HTTP {response.status_code}: {response_content}"
                    print(f"GraphQL HTTP Error: {error_msg}")
                    raise Exception(error_msg)
                
                # Parse JSON response
                try:
                    json_response = response.json()
                except json.JSONDecodeError as e:
                    error_msg = f"JSON Decode Error: {e}. Response: {response_content}"
                    print(f"GraphQL JSON Error: {error_msg}")
                    raise Exception(error_msg)
                
                # Check for GraphQL errors in response
                if "errors" in json_response:
                    errors = json_response["errors"]
                    error_details = []
                    for error in errors:
                        error_details.append({
                            "message": error.get("message", "Unknown error"),
                            "locations": error.get("locations", []),
                            "path": error.get("path", []),
                            "extensions": error.get("extensions", {})
                        })
                    
                    error_msg = f"GraphQL Errors: {json.dumps(error_details, indent=2)}"
                    print(f"GraphQL Query Errors: {error_msg}")
                    raise Exception(error_msg)
                
                return json_response
                
        except httpx.RequestError as e:
            error_msg = f"Request Error: {str(e)}"
            print(f"GraphQL Request Error: {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            if "GraphQL" not in str(e):
                error_msg = f"Unexpected Error: {str(e)}"
                print(f"GraphQL Unexpected Error: {error_msg}")
                raise Exception(error_msg)
            raise

    async def get_sections(self) -> List[Dict]:
        """Get sections using GraphQL"""
        query = """
        query {
          collection: localizedSectionJulCollection(limit: 100) { 
                items {      
                    sys { id }        
                    title  
                    key
                    subsectionsCollection(limit: 45) { 
                        total       
                        items {        
                            sys { id }        
                            title       
                            key
                        }        
                    }
                    valuesCollection(limit: 10) {
                        total
                    }
                }        
            }   
        }
        """
        
        response = await self._make_graphql_request(query)
        return response.get("data", {}).get("collection", {}).get("items", [])

    async def get_section(self, section_id: str) -> Dict:
        """Get specific section with all its data using GraphQL"""
        query = f"""
        query {{ 
            collection: localizedSectionJul(id: "{section_id}") {{
                sys {{ id }}        
                title    
                key    
                valuesCollection(limit: 650) {{        
                    items {{        
                        sys {{ id }}        
                        key        
                        value  
                        value_fr: value(locale:"fr")
                    }}        
                }}        
                subsectionsCollection(limit: 20) {{        
                    items {{        
                        sys {{ id }}        
                        title 
                        key
                        valuesCollection(limit: 250) {{        
                            items {{        
                                sys {{ id }}        
                                key 
                                originalKey
                                lineNumber       
                                value  
                                value_fr: value(locale:"fr")
                            }}        
                        }}    
                    }}        
                }}
            }}
        }}   
        """
        
        response = await self._make_graphql_request(query)
        return response.get("data", {}).get("collection", {})

    async def get_localization_entries(self, limit: int = 1250) -> List[Dict]:
        """Get localization entries using GraphQL"""
        query = f"""
        query {{
          collection: localizationEntryJulCollection(limit: {limit}) {{ 
                total
                items {{      
                    sys {{ id }}        
                    key
                    value
                    value_fr: value(locale:"fr")
                    lineNumber
                    originalKey
                    section
                    androidKey
                }}        
            }}   
        }}
        """
        
        response = await self._make_graphql_request(query)
        return response.get("data", {}).get("collection", {}).get("items", [])

    async def get_all_localization_entries(self) -> List[Dict]:
        """Get ALL localization entries using pagination"""
        all_entries = []
        skip = 0
        limit = 1000  # Maximum allowed by Contentful
        
        while True:
            query = f"""
            query {{
              collection: localizationEntryJulCollection(limit: {limit}, skip: {skip}) {{ 
                    total
                    items {{      
                        sys {{ id }}        
                        key
                        value
                        value_fr: value(locale:"fr")
                        lineNumber
                        originalKey
                        section
                        androidKey
                    }}        
                }}   
            }}
            """
            
            response = await self._make_graphql_request(query)
            collection_data = response.get("data", {}).get("collection", {})
            items = collection_data.get("items", [])
            total = collection_data.get("total", 0)
            
            if not items:
                break
                
            all_entries.extend(items)
            print(f"DEBUG: Fetched {len(items)} entries (skip: {skip}, total: {total})")
            
            if len(items) < limit or len(all_entries) >= total:
                break
                
            skip += limit
        
        print(f"DEBUG: Total entries fetched with pagination: {len(all_entries)}")
        return all_entries

    def _get_cache_key(self, method: str, **kwargs) -> str:
        """Generate cache key for method and parameters"""
        params = sorted(kwargs.items())
        return f"graph:{method}:{hash(str(params))}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self._cache_expiry:
            return False
        return datetime.now() < self._cache_expiry[cache_key]

    async def get_cached_sections(self, cache_duration: int = 300) -> List[Dict]:
        """Get sections with caching"""
        cache_key = self._get_cache_key("get_sections")
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        sections = await self.get_sections()
        
        # Cache the result
        self._cache[cache_key] = sections
        self._cache_expiry[cache_key] = datetime.now() + timedelta(seconds=cache_duration)
        
        return sections

    async def get_cached_section(self, section_id: str, cache_duration: int = 300) -> Dict:
        """Get section with caching"""
        cache_key = self._get_cache_key("get_section", section_id=section_id)
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        section = await self.get_section(section_id)
        
        # Cache the result
        self._cache[cache_key] = section
        self._cache_expiry[cache_key] = datetime.now() + timedelta(seconds=cache_duration)
        
        return section 