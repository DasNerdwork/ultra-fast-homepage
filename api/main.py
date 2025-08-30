from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from api.routers import energy, oil, petrol, status
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "https://dasnerdwork.net"
]

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(docs_url=None, redoc_url=None, title="DasNerdWork.net - PriceData & Status API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_version = "/v1"

# API-Router
app.include_router(energy.router, prefix=f"{api_version}/energy", tags=["Energy"])
app.include_router(oil.router, prefix=f"{api_version}/oil", tags=["Oil"])
app.include_router(petrol.router, prefix=f"{api_version}/petrol", tags=["Petrol"])
app.include_router(status.router, prefix=f"{api_version}/status", tags=["Status"])

# Static-Files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Eigene Swagger UI Route mit Dark Mode CSS
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_css_url="/static/swagger.css",  # hier dein Dark Mode CSS
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
    )
