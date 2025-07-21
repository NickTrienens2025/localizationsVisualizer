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
                # Handle both GraphQL format (value field) and REST API format (fields.value)
                if 'value' in entry:
                    # GraphQL format - direct value field
                    value_field = entry['value']
                elif 'fields' in entry and 'value' in entry['fields']:
                    # REST API format - nested in fields
                    value_field = entry['fields']['value']
                else:
                    continue
                
                # Handle locale value extraction
                if isinstance(value_field, dict) and locale in value_field:
                    value = value_field[locale]
                elif isinstance(value_field, str):
                    # If it's a string, use it directly (assumes it's in the requested locale)
                    value = value_field
                else:
                    continue
                
                localizations[f"{actual_section_key}.{key}"] = value
        
        localizations["__generatedAt"] = datetime.now().isoformat()
        
        return {
            "filename": f"{actual_section_key}_{locale}.json",
            "content": json.dumps(localizations, indent=2, ensure_ascii=False)
        }
