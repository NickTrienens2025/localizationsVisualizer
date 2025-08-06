import json
from datetime import datetime
from services.contentful_service import ContentfulService

class JsonExporter:
    def __init__(self, contentful_service: ContentfulService, graph_service=None):
        self.contentful_service = contentful_service
        self.graph_service = graph_service

    async def generate_json(self, section_id: str, section_key: str, locale: str) -> dict:
        # First query: Get the section to retrieve the section key (if not provided or to verify)
        if self.graph_service:
            section = await self.graph_service.get_section(section_id)
            actual_section_key = section.get("key", section_key)
        else:
            actual_section_key = section_key
        
        # Second query: Get all localization entries and filter by section key
        if self.graph_service:
            all_entries = await self.graph_service.get_all_localization_entries()
            # Filter entries by section key
            entries = [
                entry for entry in all_entries 
                if entry.get("section", "") == actual_section_key
            ]
        else:
            # Fallback to original method if graph_service not available
            entries = await self.contentful_service.get_entries_by_link_field(
                content_type="localizationEntryJUL",
                link_field="section",
                link_id=section_id
            )
        
        localizations = {}
        for entry in entries:
            key = entry.get('key', '')
            if key:
                # Handle different data formats and locale selection
                value = None
                
                if locale == 'fr':
                    # Try French value first for French locale
                    if 'value_fr' in entry:
                        # GraphQL format - direct value_fr field
                        value = entry['value_fr']
                    elif 'fields' in entry and 'value' in entry['fields']:
                        # REST API format - check for French in nested fields
                        value_field = entry['fields']['value']
                        if isinstance(value_field, dict) and 'fr' in value_field:
                            value = value_field['fr']
                
                if value is None:
                    # Fallback to English or default value
                    if 'value' in entry:
                        # GraphQL format - direct value field
                        value_field = entry['value']
                        if isinstance(value_field, dict) and locale in value_field:
                            value = value_field[locale]
                        elif isinstance(value_field, str):
                            value = value_field
                    elif 'fields' in entry and 'value' in entry['fields']:
                        # REST API format - nested in fields
                        value_field = entry['fields']['value']
                        if isinstance(value_field, dict) and locale in value_field:
                            value = value_field[locale]
                        elif isinstance(value_field, str):
                            value = value_field
                
                # Only add if we found a value
                if value:
                    # Check if key already includes the section prefix to avoid duplication
                    if key.startswith(f"{actual_section_key}."):
                        final_key = key
                    else:
                        final_key = f"{actual_section_key}.{key}"
                    
                    localizations[final_key] = value
        
        # localizations["__generatedAt"] = datetime.now().isoformat()
        
        return {
            "filename": f"{actual_section_key}_{locale}.json",
            "content": json.dumps(localizations, indent=2, ensure_ascii=False)
        }
