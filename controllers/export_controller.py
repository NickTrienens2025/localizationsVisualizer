from fastapi import Request
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from typing import Dict, Any
import zipfile
import io
from datetime import datetime
from services.enum_exporter import EnumExporter
from services.json_exporter import JsonExporter


class ExportController:
    def __init__(self, graph_service, templates: Jinja2Templates, json_exporter: JsonExporter):
        self.graph_service = graph_service
        self.templates = templates
        self.enum_exporter = EnumExporter(graph_service)
        self.json_exporter = json_exporter

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

    async def download_swift_migration_script(self, request: Request) -> Response:
        """Generate and download Swift migration script"""
        try:
            script_content = await self.enum_exporter.generate_swift_migration_script()
            
            response = Response(
                content=script_content,
                media_type="text/plain",
                headers={
                    "Content-Disposition": "attachment; filename=swift_localization_migration.sh"
                }
            )
            return response
            
        except Exception as e:
            return self.templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": f"Failed to generate Swift migration script: {str(e)}",
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

    async def download_all_json(self, request: Request, locale: str) -> Response:
        """Generate and download a ZIP file containing all JSON localization files for a specific locale"""
        
        # Default to 'en' if the locale is not 'en' or 'fr'
        effective_locale = locale if locale in ['en', 'fr'] else 'en'
        
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
            
            response = Response(
                content=zip_buffer.getvalue(),
                media_type="application/zip",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
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