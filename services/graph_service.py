import httpx
from typing import List, Dict, Any, Optional
import json

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
          collection: localizedSectionCollection(limit: 100) { 
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
          collection: localizationEntryCollection(limit: {limit}) {{ 
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
              collection: localizationEntryCollection(limit: {limit}, skip: {skip}) {{ 
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





    async def get_section_with_all_values(self, section_id: str) -> Dict:
        """Get specific section with ALL its values using pagination"""
        # First get the basic section info
        query = f"""
        query {{ 
            collection: localizedSectionJul(id: "{section_id}") {{
                sys {{ id }}        
                title    
                key    
                valuesCollection {{
                    total
                }}
                subsectionsCollection {{
                    total
                }}
            }}
        }}   
        """
        
        response = await self._make_graphql_request(query)
        section = response.get("data", {}).get("collection", {})
        
        if not section:
            return {}
        
        # Get all values with pagination
        all_values = []
        values_total = section.get('valuesCollection', {}).get('total', 0)
        skip = 0
        limit = 1000
        
        while len(all_values) < values_total:
            values_query = f"""
            query {{ 
                collection: localizedSectionJul(id: "{section_id}") {{
                    valuesCollection(limit: {limit}, skip: {skip}) {{        
                        items {{        
                            sys {{ id }}        
                            key        
                            value  
                            value_fr: value(locale:"fr")
                        }}        
                    }}
                }}
            }}   
            """
            
            values_response = await self._make_graphql_request(values_query)
            values_data = values_response.get("data", {}).get("collection", {}).get("valuesCollection", {})
            items = values_data.get("items", [])
            
            if not items:
                break
                
            all_values.extend(items)
            skip += limit
            
            if len(items) < limit:
                break
        
        # Get all subsections with pagination
        all_subsections = []
        subsections_total = section.get('subsectionsCollection', {}).get('total', 0)
        skip = 0
        limit = 50
        
        while len(all_subsections) < subsections_total:
            subsections_query = f"""
            query {{ 
                collection: localizedSectionJul(id: "{section_id}") {{
                    subsectionsCollection(limit: {limit}, skip: {skip}) {{        
                        items {{        
                            sys {{ id }}        
                            title 
                            key
                            valuesCollection {{
                                total
                            }}
                        }}        
                    }}
                }}
            }}   
            """
            
            subsections_response = await self._make_graphql_request(subsections_query)
            subsections_data = subsections_response.get("data", {}).get("collection", {}).get("subsectionsCollection", {})
            items = subsections_data.get("items", [])
            
            if not items:
                break
                
            # For each subsection, get all its values
            for subsection in items:
                subsection_values = await self.get_subsection_all_values(subsection.get('sys', {}).get('id'))
                subsection['valuesCollection'] = {"items": subsection_values}
                
            all_subsections.extend(items)
            skip += limit
            
            if len(items) < limit:
                break
        
        # Update section with all data
        section['valuesCollection'] = {"items": all_values}
        section['subsectionsCollection'] = {"items": all_subsections}
        
        print(f"DEBUG: Section {section_id} - Values: {len(all_values)}, Subsections: {len(all_subsections)}")
        
        return section

    async def get_subsection_all_values(self, subsection_id: str) -> List[Dict]:
        """Get all values for a subsection using pagination"""
        if not subsection_id:
            return []
            
        # First get the total count for the subsection's values
        query = f"""
        query {{ 
            collection: localizedSectionJul(id: "{subsection_id}") {{
                valuesCollection {{
                    total
                }}
            }}
        }}   
        """
        
        response = await self._make_graphql_request(query)
        total = response.get("data", {}).get("collection", {}).get("valuesCollection", {}).get("total", 0)
        
        all_values = []
        skip = 0
        limit = 1000
        
        while len(all_values) < total:
            values_query = f"""
            query {{ 
                collection: localizedSectionJul(id: "{subsection_id}") {{
                    valuesCollection(limit: {limit}, skip: {skip}) {{        
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
            """
            
            values_response = await self._make_graphql_request(values_query)
            values_data = values_response.get("data", {}).get("collection", {}).get("valuesCollection", {})
            items = values_data.get("items", [])
            
            if not items:
                break
                
            all_values.extend(items)
            skip += limit
            
            if len(items) < limit:
                break
        
        print(f"DEBUG: Subsection {subsection_id} - Values: {len(all_values)}")
        return all_values

    async def get_all_sections_for_export(self) -> List[Dict]:
        """Get all sections with complete data for export purposes"""
        # First get all section IDs
        sections = await self.get_sections()
        
        # Then get complete data for each section
        complete_sections = []
        for section in sections:
            section_id = section.get('sys', {}).get('id')
            if section_id:
                complete_section = await self.get_section_with_all_values(section_id)
                if complete_section:
                    complete_sections.append(complete_section)
        
        print(f"DEBUG: Retrieved {len(complete_sections)} complete sections for export")
        return complete_sections 