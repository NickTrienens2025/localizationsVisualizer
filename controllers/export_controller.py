from fastapi import Request, Query
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from typing import Dict, Any, Optional
import zipfile
import io
import os
import hashlib
import json
from datetime import datetime
from services.enum_exporter import EnumExporter
from services.json_exporter import JsonExporter


class ExportController:
    def __init__(self, graph_service, templates: Jinja2Templates, json_exporter: JsonExporter):
        self.graph_service = graph_service
        self.templates = templates
        self.enum_exporter = EnumExporter(graph_service)
        self.json_exporter = json_exporter
        self.cache_dir = "cache/downloads"
        self._ensure_cache_directory()
    
    def _ensure_cache_directory(self):
        """Ensure the cache directory exists"""
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_cache_key(self, *args) -> str:
        """Generate a cache key from arguments"""
        key_string = "_".join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cache_file_path(self, cache_key: str, file_type: str = "zip") -> str:
        """Get the full path for a cache file"""
        return os.path.join(self.cache_dir, f"{cache_key}.{file_type}")
    
    def _get_cache_metadata_path(self, cache_key: str) -> str:
        """Get the full path for cache metadata"""
        return os.path.join(self.cache_dir, f"{cache_key}_metadata.json")
    
    def _is_cache_valid(self, cache_key: str, last_updated: Optional[datetime] = None) -> bool:
        """Check if cached file is valid based on last_updated parameter"""
        metadata_path = self._get_cache_metadata_path(cache_key)
        cache_file_path = self._get_cache_file_path(cache_key)
        
        # Check if both cache file and metadata exist
        if not (os.path.exists(cache_file_path) and os.path.exists(metadata_path)):
            return False
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            cache_created = datetime.fromisoformat(metadata['created_at'])
            
            # If last_updated is provided, check if cache is newer
            if last_updated:
                return cache_created > last_updated
            
            # Default cache validity: 1 hour
            cache_age = datetime.now() - cache_created
            return cache_age.total_seconds() < 3600  # 1 hour in seconds
            
        except (json.JSONDecodeError, KeyError, ValueError):
            return False
    
    def _save_to_cache(self, cache_key: str, content: bytes, metadata: Dict[str, Any]):
        """Save content and metadata to cache"""
        cache_file_path = self._get_cache_file_path(cache_key)
        metadata_path = self._get_cache_metadata_path(cache_key)
        
        # Save the file content
        with open(cache_file_path, 'wb') as f:
            f.write(content)
        
        # Save metadata with creation timestamp
        metadata['created_at'] = datetime.now().isoformat()
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _load_from_cache(self, cache_key: str) -> Optional[bytes]:
        """Load content from cache if it exists"""
        cache_file_path = self._get_cache_file_path(cache_key)
        if os.path.exists(cache_file_path):
            with open(cache_file_path, 'rb') as f:
                return f.read()
        return None

    async def download_json(self, request: Request, section_id: str, section_key: str, locale: str) -> Response:
        """Generate and download a JSON file for a specific section and locale"""
        
        # Default to 'en' if the locale is not 'en' or 'fr'
        effective_locale = locale if locale in ['en', 'fr'] else 'en'
        
        try:
            json_data = await self.json_exporter.generate_json(section_id, section_key, effective_locale)
            
            response = Response(
                content=json_data["content"],
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename={json_data['filename']}"
                }
            )
            return response
            
        except Exception as e:
            return self.templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": f"Failed to generate JSON for section '{section_key}' and locale '{effective_locale}': {str(e)}",
                    "title": "Export Error"
                },
                status_code=500
            )

    async def download_swift_enum(self, request: Request) -> Response:
        """Generate and download Swift enum file"""
        try:
            swift_code = await self.enum_exporter.generate_swift_enum()
            
            response = Response(
                content=swift_code,
                media_type="text/plain",
                headers={
                    "Content-Disposition": "attachment; filename=Localizations.swift"
                }
            )
            return response
            
        except Exception as e:
            return self.templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": f"Failed to generate Swift enum: {str(e)}",
                    "title": "Export Error"
                },
                status_code=500
            )

    async def download_swift_testing_helper(self, request: Request) -> Response:
        """Generate and download Swift testing helper file"""
        try:
            testing_code = await self.enum_exporter.generate_swift_testing_helper()
            
            response = Response(
                content=testing_code,
                media_type="text/plain",
                headers={
                    "Content-Disposition": "attachment; filename=LocalizationsTestHelper.swift"
                }
            )
            return response
            
        except Exception as e:
            return self.templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": f"Failed to generate Swift testing helper: {str(e)}",
                    "title": "Export Error"
                },
                status_code=500
            )

    async def download_kotlin_enum(self, request: Request) -> Response:
        """Generate and download Kotlin enum file"""
        try:
            kotlin_code = await self.enum_exporter.generate_kotlin_enum()
            
            response = Response(
                content=kotlin_code,
                media_type="text/plain",
                headers={
                    "Content-Disposition": "attachment; filename=Localizations.kt"
                }
            )
            return response
            
        except Exception as e:
            return self.templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": f"Failed to generate Kotlin enum: {str(e)}",
                    "title": "Export Error"
                },
                status_code=500
            )

    async def download_kotlin_testing_helper(self, request: Request) -> Response:
        """Generate and download Kotlin testing helper file"""
        try:
            testing_code = await self.enum_exporter.generate_kotlin_testing_helper()
            
            response = Response(
                content=testing_code,
                media_type="text/plain",
                headers={
                    "Content-Disposition": "attachment; filename=LocalizationTestHelper.kt"
                }
            )
            return response
            
        except Exception as e:
            return self.templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": f"Failed to generate Kotlin testing helper: {str(e)}",
                    "title": "Export Error"
                },
                status_code=500
            )



    async def download_python_migration_script(self, request: Request) -> Response:
        """Generate and download Python migration script"""
        try:
            script_content = await self.enum_exporter.generate_python_migration_script()
            
            response = Response(
                content=script_content,
                media_type="text/plain",
                headers={
                    "Content-Disposition": "attachment; filename=swift_localization_migration.py"
                }
            )
            return response
            
        except Exception as e:
            return self.templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": f"Failed to generate Python migration script: {str(e)}",
                    "title": "Export Error"
                },
                status_code=500
            )

    async def preview_swift_enum(self, request: Request) -> Dict[str, Any]:
        """Preview Swift enum code in JSON format"""
        try:
            swift_code = await self.enum_exporter.generate_swift_enum()
            
            return {
                "success": True,
                "code": swift_code,
                "language": "swift",
                "filename": "Localizations.swift"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                                "code": None
            }

    async def download_all_json(self, request: Request, locale: str, last_updated: Optional[str] = None) -> Response:
        """Generate and download a ZIP file containing all JSON localization files for a specific locale"""
        
        # Default to 'en' if the locale is not 'en' or 'fr'
        effective_locale = locale if locale in ['en', 'fr'] else 'en'
        
        # Parse last_updated parameter if provided
        last_updated_dt = None
        if last_updated:
            try:
                last_updated_dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            except ValueError:
                # If invalid date format, ignore and proceed without cache check
                pass
        
        # Generate cache key for locale-specific zip
        cache_key = self._get_cache_key("locale_zip", effective_locale)
        
        # Check if we have a valid cached version
        if self._is_cache_valid(cache_key, last_updated_dt):
            cached_content = self._load_from_cache(cache_key)
            if cached_content:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"localizations_{effective_locale}_{timestamp}.zip"
                
                return Response(
                    content=cached_content,
                    media_type="application/zip",
                    headers={
                        "Content-Disposition": f"attachment; filename={filename}",
                        "X-Cache-Status": "HIT"
                    }
                )
        
        try:
            # Get all sections
            sections = await self.graph_service.get_sections()
            
            # Get all localization entries to filter by sections that have content
            all_entries = await self.graph_service.get_all_localization_entries()
            
            # Group entries by section
            entries_by_section = {}
            for entry in all_entries:
                section_key = entry.get("section", "")
                if section_key:
                    if section_key not in entries_by_section:
                        entries_by_section[section_key] = []
                    entries_by_section[section_key].append(entry)
            
            # Create ZIP file in memory
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                files_added = 0
                
                for section in sections:
                    section_id = section.get("sys", {}).get("id", "")
                    section_key = section.get("key", "")
                    section_title = section.get("title", "")
                    
                    # Check if this section has localization entries
                    section_entries = entries_by_section.get(section_key, [])
                    if not section_entries:
                        continue
                    
                    # Check if any entries have values for this locale
                    has_content = False
                    for entry in section_entries:
                        if effective_locale == "en" and entry.get("value"):
                            has_content = True
                            break
                        elif effective_locale == "fr" and entry.get("value_fr"):
                            has_content = True
                            break
                    
                    if not has_content:
                        continue
                    
                    try:
                        # Generate JSON for this section
                        json_data = await self.json_exporter.generate_json(section_id, section_key, effective_locale)
                        
                        # Add to ZIP
                        zip_file.writestr(json_data["filename"], json_data["content"])
                        files_added += 1
                        
                    except Exception as e:
                        print(f"Warning: Failed to generate JSON for section '{section_key}': {str(e)}")
                        continue
                
                # Add a manifest file to the ZIP
                manifest = {
                    "generated_at": datetime.now().isoformat(),
                    "locale": effective_locale,
                    "total_files": files_added,
                    "service": "Contentful Localization Service",
                    "version": "1.0.0"
                }
                
                import json
                zip_file.writestr("manifest.json", json.dumps(manifest, indent=2))
            
            zip_buffer.seek(0)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"localizations_{effective_locale}_{timestamp}.zip"
            
            # Get the zip content
            zip_content = zip_buffer.getvalue()
            
            # Save to cache
            cache_metadata = {
                "filename": filename,
                "total_files": files_added,
                "locale": effective_locale,
                "generated_for": f"locale_zip_{effective_locale}"
            }
            self._save_to_cache(cache_key, zip_content, cache_metadata)
            
            response = Response(
                content=zip_content,
                media_type="application/zip",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "X-Cache-Status": "MISS"
                }
            )
            return response
            
        except Exception as e:
            return self.templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": f"Failed to generate ZIP file for locale '{effective_locale}': {str(e)}",
                    "title": "Export Error"
                },
                status_code=500
            )

    async def download_all_json_single_zip(self, request: Request, last_updated: Optional[str] = None) -> Response:
        """Generate and download a ZIP file containing all JSON localization files for all locales"""
        
        # Parse last_updated parameter if provided
        last_updated_dt = None
        if last_updated:
            try:
                last_updated_dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            except ValueError:
                # If invalid date format, ignore and proceed without cache check
                pass
        
        # Generate cache key for all locales zip
        cache_key = self._get_cache_key("all_locales_zip")
        
        # Check if we have a valid cached version
        if self._is_cache_valid(cache_key, last_updated_dt):
            cached_content = self._load_from_cache(cache_key)
            if cached_content:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"localizations_all_locales_{timestamp}.zip"
                
                return Response(
                    content=cached_content,
                    media_type="application/zip",
                    headers={
                        "Content-Disposition": f"attachment; filename={filename}",
                        "X-Cache-Status": "HIT"
                    }
                )
        
        try:
            # Get all sections
            sections = await self.graph_service.get_sections()
            
            # Get all localization entries to filter by sections that have content
            all_entries = await self.graph_service.get_all_localization_entries()
            
            # Group entries by section
            entries_by_section = {}
            for entry in all_entries:
                section_key = entry.get("section", "")
                if section_key:
                    if section_key not in entries_by_section:
                        entries_by_section[section_key] = []
                    entries_by_section[section_key].append(entry)
            
            # Create ZIP file in memory
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                files_added = 0
                locales = ['en', 'fr']  # Support both English and French
                
                for section in sections:
                    section_id = section.get("sys", {}).get("id", "")
                    section_key = section.get("key", "")
                    section_title = section.get("title", "")
                    
                    # Check if this section has localization entries
                    section_entries = entries_by_section.get(section_key, [])
                    if not section_entries:
                        continue
                    
                    # Generate JSON for each locale
                    for locale in locales:
                        # Check if any entries have values for this locale
                        has_content = False
                        for entry in section_entries:
                            if locale == "en" and entry.get("value"):
                                has_content = True
                                break
                            elif locale == "fr" and entry.get("value_fr"):
                                has_content = True
                                break
                        
                        if not has_content:
                            continue
                        
                        try:
                            # Generate JSON for this section and locale
                            json_data = await self.json_exporter.generate_json(section_id, section_key, locale)
                            
                            # Add to ZIP directly in root (no locale subfolder)
                            zip_file.writestr(json_data['filename'], json_data["content"])
                            files_added += 1
                            
                        except Exception as e:
                            print(f"Warning: Failed to generate JSON for section '{section_key}' locale '{locale}': {str(e)}")
                            continue
                
                # Add a manifest file to the ZIP
                manifest = {
                    "generated_at": datetime.now().isoformat(),
                    "locales": locales,
                    "total_files": files_added,
                    "service": "Contentful Localization Service",
                    "version": "1.0.0",
                    "structure": "All localization files are in the root directory. Locale is indicated by filename suffix (_en.json, _fr.json)"
                }
                
                import json
                zip_file.writestr("manifest.json", json.dumps(manifest, indent=2))
            
            zip_buffer.seek(0)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"localizations_all_locales_{timestamp}.zip"
            
            # Get the zip content
            zip_content = zip_buffer.getvalue()
            
            # Save to cache
            cache_metadata = {
                "filename": filename,
                "total_files": files_added,
                "locales": locales,
                "generated_for": "all_locales_zip"
            }
            self._save_to_cache(cache_key, zip_content, cache_metadata)
            
            response = Response(
                content=zip_content,
                media_type="application/zip",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "X-Cache-Status": "MISS"
                }
            )
            return response
            
        except Exception as e:
            return self.templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": f"Failed to generate single ZIP file with all locales: {str(e)}",
                    "title": "Export Error"
                },
                status_code=500
            )

    async def preview_kotlin_enum(self, request: Request) -> Dict[str, Any]:
        """Preview Kotlin enum code in JSON format"""
        try:
            kotlin_code = await self.enum_exporter.generate_kotlin_enum()
            
            return {
                "success": True,
                "code": kotlin_code,
                "language": "kotlin",
                "filename": "Localizations.kt"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "code": None
            } 