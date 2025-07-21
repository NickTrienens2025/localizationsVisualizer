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
            sections = await self.graph_service.get_sections()
            
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
            section = await self.graph_service.get_section(section_id)
            
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
            sections = await self.graph_service.get_sections()
            
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

    async def get_manifest(self) -> Dict:
        """Generate a manifest JSON listing all available JSON localization files"""
        try:
            # Get all sections
            sections = await self.graph_service.get_sections()
            
            # Get all localization entries to determine which sections have content
            all_entries = await self.graph_service.get_all_localization_entries()
            
            # Group entries by section to determine which sections have content
            entries_by_section = {}
            for entry in all_entries:
                section_key = entry.get("section", "")
                if section_key:
                    if section_key not in entries_by_section:
                        entries_by_section[section_key] = []
                    entries_by_section[section_key].append(entry)
            
            # Supported locales
            supported_locales = ["en", "fr"]
            
            # Build manifest data
            manifest_files = []
            total_files = 0
            
            for section in sections:
                section_id = section.get("sys", {}).get("id", "")
                section_key = section.get("key", "")
                section_title = section.get("title", "")
                
                # Check if this section has localization entries
                section_entries = entries_by_section.get(section_key, [])
                if not section_entries:
                    continue
                
                # For each supported locale, check if there are entries with values
                available_locales = []
                for locale in supported_locales:
                    # Check if any entries have values for this locale
                    has_content = False
                    for entry in section_entries:
                        if locale == "en" and entry.get("value"):
                            has_content = True
                            break
                        elif locale == "fr" and entry.get("value_fr"):
                            has_content = True
                            break
                    
                    if has_content:
                        available_locales.append(locale)
                
                # Create file entries for available locales
                files_for_section = []
                for locale in available_locales:
                    filename = f"{section_key}_{locale}.json"
                    download_url = f"/download/json/{section_id}/{section_key}/{locale}"
                    
                    files_for_section.append({
                        "locale": locale,
                        "filename": filename,
                        "download_url": download_url,
                        "content_type": "application/json"
                    })
                    total_files += 1
                
                if files_for_section:
                    manifest_files.append({
                        "section": {
                            "id": section_id,
                            "key": section_key,
                            "title": section_title
                        },
                        "entry_count": len(section_entries),
                        "available_locales": available_locales,
                        "files": files_for_section
                    })
            
            # Generate manifest
            from datetime import datetime
            manifest = {
                "manifest_version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "service": {
                    "name": "Contentful Localization Service",
                    "version": "1.0.0"
                },
                "supported_locales": supported_locales,
                "statistics": {
                    "total_sections": len(manifest_files),
                    "total_files": total_files,
                    "total_entries": len(all_entries)
                },
                "files": manifest_files
            }
            
            return {
                "success": True,
                "data": manifest
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": None
            } 