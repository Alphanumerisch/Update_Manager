from fastapi import FastAPI
from app.routes import router
import sys

app = FastAPI(
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# API-Routen auslagern
print("🚀 FastAPI Server gestartet!", file=sys.stderr)
sys.stderr.flush()

app.include_router(router)

#if __name__ == "__main__":
#    import uvicorn
#    uvicorn.run(app, host="0.0.0.0", port=8000)
