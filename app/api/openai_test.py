from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from ..services.openai_client import test_api_connection

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@router.get("/test-openai", response_class=HTMLResponse)
def test_openai_page(request: Request):
    """
    Render the API test page.
    """
    return templates.TemplateResponse("test_api.html", {"request": request, "title": "API Test"})

@router.post("/test-openai-run", response_class=HTMLResponse)
def test_openai_run(request: Request):
    """
    Run the API connection test and show result.
    """
    result = test_api_connection()
    return templates.TemplateResponse("test_api.html", {
        "request": request, 
        "title": "API Test Result",
        "result": result
    })
