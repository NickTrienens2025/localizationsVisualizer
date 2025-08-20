import json
import traceback
from fastapi import Request
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any

class SectionController:
    def __init__(self, contentful_service, graph_service, templates: Jinja2Templates, space_id: str, environment_id: str):
        self.contentful_service = contentful_service
        self.graph_service = graph_service
        self.templates = templates
        self.space_id = space_id
        self.environment_id = environment_id

    async def sections_view(self, request: Request):
        """Render sections overview page"""
        try:
            sections = await self.graph_service.get_sections()
            
            # Process sections for display
            processed_sections = []
            for section in sections:
                if isinstance(section, dict):
                    try:
                        values = section.get("valuesCollection", {}).get("items", [])
                        if not isinstance(values, list):
                            values = []
                    except Exception:
                        values = []
                        
                    processed_sections.append({
                        "id": section.get("sys", {}).get("id", ""),
                        "title": section.get("title", ""),
                        "key": section.get("key", ""),
                        "values_count": len(values)
                    })

            return self.templates.TemplateResponse(
                "sections_overview.html",
                {
                    "request": request,
                    "space_id": self.space_id,
                    "environment_id": self.environment_id,
                    "sections": processed_sections,
                    "title": "Sections Overview"
                }
            )
        except Exception as e:
            # Get traceback information
            tb_list = traceback.extract_tb(e.__traceback__)
            line_info = []
            for tb in tb_list[-3:]:  # Show last 3 frames
                line_info.append({
                    "filename": tb.filename,
                    "line_number": tb.lineno,
                    "function": tb.name,
                    "line": tb.line
                })
            
            return self.templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": str(e),
                    "traceback": line_info,
                    "title": "Error"
                }
            )

    async def section_view(self, request: Request, section_id: str):
        """Render individual section detail view"""
        try:
            # GraphQL query string for debugging
            graphql_query = f'''
            query {{ 
                collection: localizedSection(id: "{section_id}") {{
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
            '''
            section = await self.graph_service.get_section(section_id)
            
            if not section:
                return self.templates.TemplateResponse(
                    "error.html",
                    {
                        "request": request,
                        "error": "Section not found",
                        "title": "Error"
                    }
                )

            # Get the section key to find related localization entries
            section_key = section.get("key", "")
            print(f"DEBUG: Section key: {section_key}")
            
            # Fetch all localization entries and filter by section
            graphql_errors = None
            try:
                all_entries = await self.graph_service.get_all_localization_entries()
                print(f"DEBUG: Total entries fetched: {len(all_entries)}")
                section_entries = []
                
                for entry in all_entries:
                    entry_section = entry.get("section", "")
                    
                    if entry_section == section_key:
                        section_entries.append({
                            "id": entry.get("sys", {}).get("id", ""),
                            "key": entry.get("key", ""),
                            "value_en": entry.get("value", ""),
                            "value_fr": entry.get("value_fr", ""),
                            "line_number": entry.get("lineNumber", ""),
                            "original_key": entry.get("originalKey", ""),
                            "android_key": entry.get("androidKey", "")
                        })
                
                print(f"DEBUG: Section entries found: {len(section_entries)}")
                if section_entries:
                    print(f"DEBUG: First entry key: {section_entries[0]['key']}")
            except Exception as e:
                error_msg = str(e)
                print(f"Error fetching localization entries: {error_msg}")
                section_entries = []
                graphql_errors = error_msg

            # Process section data with better error handling
            try:
                values = section.get("valuesCollection", {}).get("items", [])
                if not isinstance(values, list):
                    values = []
            except Exception:
                values = []
                
            try:
                subsections = section.get("subsectionsCollection", {}).get("items", [])
                if not isinstance(subsections, list):
                    subsections = []
            except Exception:
                subsections = []
            
            # Use the manually fetched entries instead of the GraphQL values
            processed_values = section_entries if isinstance(section_entries, list) else []
            print(f"DEBUG: Final processed values count: {len(processed_values)}")
            print(f"DEBUG: processed_values type: {type(processed_values)}")
            print(f"DEBUG: processed_values is iterable: {hasattr(processed_values, '__iter__')}")
            if processed_values:
                print(f"DEBUG: First processed value: {processed_values[0]}")
            
            # Ensure we have a clean list of dictionaries for the template
            template_values = []
            if isinstance(processed_values, list):
                for value in processed_values:
                    if isinstance(value, dict):
                        template_values.append(value)
            print(f"DEBUG: template_values count: {len(template_values)}")
            print(f"DEBUG: template_values type: {type(template_values)}")

            processed_subsections = []
            for subsection in subsections:
                if isinstance(subsection, dict):
                    subsection_key = subsection.get("key", "")
                    print(f"DEBUG: Processing subsection with key: {subsection_key}")
                    
                    # Try GraphQL values first
                    try:
                        subsection_values = subsection.get("valuesCollection", {}).get("items", [])
                        if not isinstance(subsection_values, list):
                            subsection_values = []
                        print(f"DEBUG: GraphQL subsection values count: {len(subsection_values)}")
                    except Exception as e:
                        print(f"DEBUG: Error getting GraphQL subsection values: {e}")
                        subsection_values = []
                    
                    # If no GraphQL values, try filtering from all entries by subsection key
                    if not subsection_values and 'all_entries' in locals():
                        print(f"DEBUG: No GraphQL values, filtering from all entries for subsection: {subsection_key}")
                        for entry in all_entries:
                            entry_section = entry.get("section", "")
                            if entry_section == subsection_key:
                                subsection_values.append(entry)
                        print(f"DEBUG: Found {len(subsection_values)} entries for subsection {subsection_key}")
                        
                    processed_subsection_values = []
                    
                    for value in subsection_values:
                        if isinstance(value, dict):
                            processed_subsection_values.append({
                                "id": value.get("sys", {}).get("id", ""),
                                "key": value.get("key", ""),
                                "original_key": value.get("originalKey", ""),
                                "line_number": value.get("lineNumber", ""),
                                "value_en": value.get("value", ""),
                                "value_fr": value.get("value_fr", "")
                            })

                    print(f"DEBUG: Final subsection {subsection_key} processed values: {len(processed_subsection_values)}")
                    processed_subsections.append({
                        "id": subsection.get("sys", {}).get("id", ""),
                        "title": subsection.get("title", ""),
                        "key": subsection.get("key", ""),
                        "processed_values": processed_subsection_values if isinstance(processed_subsection_values, list) else []
                    })

            return self.templates.TemplateResponse(
                "section_detail.html",
                {
                    "request": request,
                    "space_id": self.space_id,
                    "environment_id": self.environment_id,
                    "section": {
                        "id": section.get("sys", {}).get("id", ""),
                        "title": section.get("title", ""),
                        "key": section.get("key", ""),
                        "subsections": processed_subsections
                    },
                    "values": template_values,
                    "title": f"Section: {section.get('title', 'Unknown')}",
                    "graphql_query": graphql_query,
                    "debug_info": {
                        "section_key": section_key,
                        "total_entries_fetched": len(all_entries) if 'all_entries' in locals() else 0,
                        "section_entries_found": len(section_entries) if 'section_entries' in locals() else 0,
                        "graphql_errors": graphql_errors,
                        "processed_values_count": len(template_values),
                        "processed_values_type": str(type(template_values)),
                        "processed_values_is_iterable": hasattr(template_values, '__iter__')
                    }
                }
            )
        except Exception as e:
            # Get traceback information
            tb_list = traceback.extract_tb(e.__traceback__)
            line_info = []
            for tb in tb_list[-3:]:  # Show last 3 frames
                line_info.append({
                    "filename": tb.filename,
                    "line_number": tb.lineno,
                    "function": tb.name,
                    "line": tb.line
                })
            
            return self.templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": str(e),
                    "traceback": line_info,
                    "title": "Error"
                }
            )

    async def everything(self):
        """Generate all localization files"""
        try:
            sections = await self.graph_service.get_sections()
            
            # Process all sections and their data
            all_data = []
            for section in sections:
                section_id = section.get("sys", {}).get("id")
                if section_id:
                    section_detail = await self.graph_service.get_section(section_id)
                    all_data.append(section_detail)
            
            # Save to JSON file
            with open("mainSections.json", "w", encoding="utf-8") as f:
                json.dump(all_data, f, indent=2, ensure_ascii=False)
                
            return all_data
        except Exception as e:
            print(f"Error generating everything: {e}")
            return [] 