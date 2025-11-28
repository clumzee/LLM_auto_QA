from fastapi import FastAPI
from routers import gherkin_router
from core.config import Settings

app = FastAPI()


@app.get("/accessible")
async def root():
    return {"status": "ok"}

app.include_router(gherkin_router, prefix=f"/gherkin", tags=["gherkin"])