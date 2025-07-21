from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from services.contentful_service import ContentfulService

class DownloadsController:
    def __init__(self, contentful_service: ContentfulService, templates: Jinja2Templates):
        self.contentful_service = contentful_service
        self.templates = templates

    async def downloads_page(self, request: Request) -> HTMLResponse:
        """Renders the downloads page with a list of sections."""
        sections = await self.contentful_service.get_all_entries("localizedSectionJUL")
        return self.templates.TemplateResponse(
            "downloads.html",
            {
                "request": request,
                "sections": sections,
                "title": "Download Localizations"
            }
        )
