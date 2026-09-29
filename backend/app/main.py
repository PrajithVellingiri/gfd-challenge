from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import health_router, requests_router

app = FastAPI(
    title="GFD Challenge - Digital Public Infrastructure API",
    description="Backend API for Citizen Requests, Spatial Data, and Infrastructure Governance (Phase 1).",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(health_router)
app.include_router(requests_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "GFD Challenge DPI API",
        "phase": "Phase 1 - Database + Storage Foundation",
        "status": "online",
        "documentation": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
