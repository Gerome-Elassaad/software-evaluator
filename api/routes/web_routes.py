from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from typing import Optional
import os

from product_evaluator.utils.template_engine import render_template

# Create router
router = APIRouter()


# Home page
@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """Render the home page."""
    return render_template(request, "home.html")


# Login page
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the login page."""
    return render_template(request, "login.html")


# Register page
@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Render the register page."""
    return render_template(request, "register.html")


# Profile page
@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """Render the profile page."""
    return render_template(request, "profile.html")


# Products page
@router.get("/products", response_class=HTMLResponse)
async def products_page(request: Request):
    """Render the products page."""
    return render_template(request, "products.html")


# Evaluations page
@router.get("/evaluations", response_class=HTMLResponse)
async def evaluations_page(request: Request):
    """Render the evaluations page."""
    return render_template(request, "evaluations.html")


# New evaluation page
@router.get("/evaluations/new", response_class=HTMLResponse)
async def new_evaluation_page(request: Request):
    """Render the new evaluation page."""
    return render_template(request, "new_evaluation.html")


# View evaluation page
@router.get("/evaluations/{evaluation_id}", response_class=HTMLResponse)
async def view_evaluation_page(request: Request, evaluation_id: str):
    """Render the view evaluation page."""
    return render_template(request, "view_evaluation.html")


# Edit evaluation page (for future implementation)
@router.get("/evaluations/{evaluation_id}/edit", response_class=HTMLResponse)
async def edit_evaluation_page(request: Request, evaluation_id: str):
    """Render the edit evaluation page."""
    # For MVP, redirect to the view page
    return RedirectResponse(url=f"/evaluations/{evaluation_id}")


# Serve common JavaScript file
@router.get("/static/js/common.js")
async def common_js():
    """Serve the common JavaScript file."""
    js_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        "static", "js", "common.js"
    )
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(js_path), exist_ok=True)
    
    # If file doesn't exist, create it
    if not os.path.exists(js_path):
        with open(js_path, "w") as f:
            f.write("""/**
 * Common JavaScript functions for Product Evaluator
 */

// Global API helper functions
const API = {
    // ... (contents from common.js)
};
""")
    
    return FileResponse(js_path, media_type="application/javascript")


# Serve custom CSS file
@router.get("/static/css/custom.css")
async def custom_css():
    """Serve the custom CSS file."""
    css_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        "static", "css", "custom.css"
    )
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(css_path), exist_ok=True)
    
    # If file doesn't exist, create it
    if not os.path.exists(css_path):
        with open(css_path, "w") as f:
            f.write("""/* Custom styles for Product Evaluator */

/* ... (contents from custom.css) */
""")
    
    return FileResponse(css_path, media_type="text/css")


# Favicon
@router.get("/favicon.ico")
async def favicon():
    """Serve the favicon."""
    favicon_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        "static", "favicon.ico"
    )
    
    # If file doesn't exist, return a 404
    if not os.path.exists(favicon_path):
        return HTMLResponse(status_code=404)
    
    return FileResponse(favicon_path)


# Catch-all route for invalid paths
@router.get("/{path:path}", response_class=HTMLResponse)
async def catch_all(request: Request, path: str):
    """Handle all other routes with a 404 page."""
    return render_template(
        request, 
        "404.html", 
        {"status_code": 404, "detail": f"Page '/{path}' not found"}
    )