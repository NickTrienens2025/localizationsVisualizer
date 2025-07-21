from typing import List, Dict, Any, Optional

class JSONController:
    def __init__(self, contentful_service, graph_service):
        self.contentful_service = contentful_service
        self.graph_service = graph_service

    async def get_entries(self, content_type: Optional[str] = None) -> Dict:
        """Get entries as JSON"""
        try:
            if content_type:
                entries = await self.contentful_service.get_all_entries(content_type)
            else:
                entries = await self.contentful_service.get_all_entries()
            
            return {
                "success": True,
                "data": entries,
                "count": len(entries)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": []
            }

    async def get_sections(self) -> Dict:
        """Get sections as JSON"""
        try:
            sections = await self.graph_service.get_cached_sections()
            
            return {
                "success": True,
                "data": sections,
                "count": len(sections)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": []
            }

    async def get_section(self, section_id: str) -> Dict:
        """Get specific section as JSON"""
        try:
            section = await self.graph_service.get_cached_section(section_id)
            
            if not section:
                return {
                    "success": False,
                    "error": "Section not found",
                    "data": None
                }
            
            return {
                "success": True,
                "data": section
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": None
            }

    async def get_localization_files(self) -> Dict:
        """Get all localization files as JSON"""
        try:
            # Get all sections
            sections = await self.graph_service.get_cached_sections()
            
            # Get all localization entries
            entries = await self.graph_service.get_localization_entries()
            
            # Organize by language
            localization_files = {
                "en": {},
                "fr": {}
            }
            
            # Process entries
            for entry in entries:
                key = entry.get("key")
                if key:
                    localization_files["en"][key] = entry.get("value", "")
                    localization_files["fr"][key] = entry.get("value_fr", "")
            
            return {
                "success": True,
                "data": {
                    "sections": sections,
                    "localization_files": localization_files,
                    "stats": {
                        "total_sections": len(sections),
                        "total_entries": len(entries),
                        "total_keys_en": len(localization_files["en"]),
                        "total_keys_fr": len(localization_files["fr"])
                    }
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": None
            } 