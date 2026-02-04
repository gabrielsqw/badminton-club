import os

from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

from badminton_club.api.routes import users, sessions, availability, locations

app = FastAPI(
    title="Badminton Club API", docs_url="/api/docs", openapi_url="/api/openapi.json"
)

API_KEY = os.environ.get("API_KEY", "")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(key: str | None = Security(api_key_header)):
    if API_KEY and key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")


app.include_router(users.router, prefix="/api", dependencies=[Depends(verify_api_key)])
app.include_router(
    sessions.router, prefix="/api", dependencies=[Depends(verify_api_key)]
)
app.include_router(
    availability.router, prefix="/api", dependencies=[Depends(verify_api_key)]
)
app.include_router(
    locations.router, prefix="/api", dependencies=[Depends(verify_api_key)]
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
