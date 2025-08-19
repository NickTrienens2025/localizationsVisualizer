from fastapi import Request
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any
import json

class TableController:
    def __init__(self, contentful_service, templates: Jinja2Templates, space_id: str, environment_id: str, contentful_models: dict = None):
        self.contentful_service = contentful_service
        self.templates = templates
        self.space_id = space_id
        self.environment_id = environment_id
        self.contentful_models = contentful_models or {
            "localizationEntry": "localizationEntryJul",
            "localizedSection": "localizedSectionJul"
        }

    async def list(self, request: Request):
        """Main dashboard page"""
        return self.templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "title": "Contentful Localization Dashboard"
            }
        )

    async def table(self, request: Request, entries: List[Dict]):
        """Render table view of localization entries"""
        # Sort entries by line number
        sorted_entries = sorted(entries, key=lambda x: self._get_line_number(x))
        
        # Get sections to create a mapping from section names to section IDs
        try:
            sections = await self.contentful_service.get_all_entries(self.contentful_models["localizedSection"])
            section_mapping = {}
            for section in sections:
                fields = section.get("fields", {})
                section_key = self._get_field_value(fields, "key", "en-US")
                section_id = section.get("sys", {}).get("id")
                if section_key and section_id:
                    section_mapping[section_key] = section_id
        except Exception as e:
            print(f"Error fetching sections for mapping: {e}")
            section_mapping = {}
        
        # Process entries for display
        processed_entries = []
        for entry in sorted_entries:
            fields = entry.get("fields", {})
            section_name = self._get_field_value(fields, "section", "en-US")
            section_id = section_mapping.get(section_name, "")
            
            processed_entries.append({
                "id": entry.get("sys", {}).get("id"),
                "key": self._get_field_value(fields, "key", "en-US"),
                "line_number": self._get_field_value(fields, "lineNumber", "en-US"),
                "section": section_name,
                "section_id": section_id,
                "value_en": self._get_field_value(fields, "value", "en-US"),
                "value_fr": self._get_field_value(fields, "value", "fr"),
                "original_key": self._get_field_value(fields, "originalKey", "en-US"),
                "android_key": self._get_field_value(fields, "androidKey", "en-US")
            })

        return self.templates.TemplateResponse(
            "table.html",
            {
                "request": request,
                "space_id": self.space_id,
                "environment_id": self.environment_id,
                "entries": processed_entries,
                "title": "Localization Entries"
            }
        )

    async def section(self, request: Request, entries: List[Dict]):
        """Render table view of sections"""
        # Sort entries by title
        sorted_entries = sorted(entries, key=lambda x: self._get_field_value(x.get("fields", {}), "title", "en-US"))
        
        # Process entries for display
        processed_entries = []
        for entry in sorted_entries:
            fields = entry.get("fields", {})
            values = fields.get("values", {})
            values_count = len(values.get("en-US", [])) if values.get("en-US") else 0
            
            processed_entries.append({
                "id": entry.get("sys", {}).get("id"),
                "title": self._get_field_value(fields, "title", "en-US"),
                "key": self._get_field_value(fields, "key", "en-US"),
                "values_count": values_count
            })

        return self.templates.TemplateResponse(
            "sections_table.html",
            {
                "request": request,
                "space_id": self.space_id,
                "environment_id": self.environment_id,
                "entries": processed_entries,
                "title": "Localization Sections"
            }
        )

    def _get_field_value(self, fields: Dict, field_name: str, locale: str = "en-US") -> str:
        """Safely get field value from Contentful entry"""
        field = fields.get(field_name, {})
        if isinstance(field, dict):
            return field.get(locale, "")
        return str(field) if field else ""

    def _get_line_number(self, entry: Dict) -> int:
        """Get line number from entry, defaulting to 0"""
        try:
            line_number = self._get_field_value(entry.get("fields", {}), "lineNumber", "en-US")
            return int(line_number) if line_number else 0
        except (ValueError, TypeError):
            return 0 