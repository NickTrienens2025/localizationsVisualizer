from fastapi import Request
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from typing import Dict, Any
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