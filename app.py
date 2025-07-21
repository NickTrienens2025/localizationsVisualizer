import os
import asyncio
import traceback
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import uvicorn

from services.contentful_service import ContentfulService
from services.graph_service import GraphService
from controllers.table_controller import TableController
from controllers.section_controller import SectionController
from controllers.json_controller import JSONController

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Contentful Localization Service",
    description="A service for managing and viewing Contentful localization files",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Get environment variables
SPACE_ID = os.getenv("SPACE_ID")
ENVIRONMENT_ID = os.getenv("ENVIRONMENT_ID", "master")

# Initialize services
contentful_service = ContentfulService(
    space_id=SPACE_ID,
    environment_id=ENVIRONMENT_ID,
    access_token=os.getenv("TOKEN")
)

graph_service = GraphService(
    space_id=SPACE_ID,
    environment_id=ENVIRONMENT_ID,
    access_token=os.getenv("GRAPH_TOKEN")
)

# Initialize controllers
table_controller = TableController(contentful_service, templates)
section_controller = SectionController(contentful_service, graph_service, templates)
json_controller = JSONController(contentful_service, graph_service)

# Global template context
def get_template_context(request: Request, **kwargs):
    """Get common template context with environment variables"""
    context = {
        "request": request,
        "space_id": SPACE_ID,
        "environment_id": ENVIRONMENT_ID,
        **kwargs
    }
    return context

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to capture traceback information"""
    # Get the full traceback
    tb_list = traceback.extract_tb(exc.__traceback__)
    
    # Extract line number information
    line_info = []
    for tb in tb_list[-3:]:  # Show last 3 frames
        line_info.append({
            "filename": tb.filename,
            "line_number": tb.lineno,
            "function": tb.name,
            "line": tb.line
        })
    
    return templates.TemplateResponse(
        "error.html",
        get_template_context(
            request,
            error=str(exc),
            traceback=line_info,
            title="Error"
        ),
        status_code=500
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse(
        "dashboard.html",
        get_template_context(request, title="Contentful Localization Dashboard")
    )

@app.get("/table", response_class=HTMLResponse)
async def table_view(request: Request):
    """Table view of all localization entries"""
    entries = await contentful_service.get_all_entries("localizationEntryJUL")
    response = await table_controller.table(request, entries)
    # Update the response context to include environment variables
    response.context.update(get_template_context(request))
    return response

@app.get("/sections", response_class=HTMLResponse)
async def sections_view(request: Request):
    """Sections view"""
    entries = await contentful_service.get_all_entries("localizedSectionJUL")
    response = await table_controller.section(request, entries)
    # Update the response context to include environment variables
    response.context.update(get_template_context(request))
    return response

@app.get("/sections/view", response_class=HTMLResponse)
async def sections_overview(request: Request):
    """Sections overview page"""
    response = await section_controller.sections_view(request)
    # Update the response context to include environment variables
    response.context.update(get_template_context(request))
    return response

@app.get("/section/{section_id}/view", response_class=HTMLResponse)
async def section_detail(request: Request, section_id: str):
    """Individual section detail view"""
    response = await section_controller.section_view(request, section_id)
    # Update the response context to include environment variables
    response.context.update(get_template_context(request))
    return response

# JSON API endpoints
@app.get("/api/entries")
async def get_entries(content_type: str = None):
    """Get entries as JSON"""
    return await json_controller.get_entries(content_type)

@app.get("/api/sections")
async def get_sections():
    """Get sections as JSON"""
    return await json_controller.get_sections()

@app.get("/api/section/{section_id}")
async def get_section(section_id: str):
    """Get specific section as JSON"""
    return await json_controller.get_section(section_id)

@app.get("/api/localization")
async def get_localization_files():
    """Get all localization files as JSON"""
    return await json_controller.get_localization_files()

@app.get("/test-error")
async def test_error():
    """Test route to demonstrate error handling with line numbers"""
    # This will trigger an error to test our error handling
    raise ValueError("This is a test error to demonstrate line number display")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8888))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    ) 