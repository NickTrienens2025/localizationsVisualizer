from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from services.contentful_service import ContentfulService

class DownloadsController:
    def __init__(self, contentful_service: ContentfulService, templates: Jinja2Templates, space_id: str, environment_id: str):
        self.contentful_service = contentful_service
        self.templates = templates
        self.space_id = space_id
        self.environment_id = environment_id

    async def downloads_page(self, request: Request) -> HTMLResponse:
        """Renders the downloads page with a list of sections."""
        sections = await self.contentful_service.get_all_entries("localizedSectionJUL")
        return self.templates.TemplateResponse(
            "downloads.html",
            {
                "request": request,
                "space_id": self.space_id,
                "environment_id": self.environment_id,
                "sections": sections,
                "title": "Download Localizations"
            }
        )
