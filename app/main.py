"""Minimal API served locally and on Azure App Service."""

from fastapi import FastAPI

app = FastAPI(
    title="AssetDB API",
    description="A minimal FastAPI app deployed from GitHub to Azure App Service.",
    version="0.1.0",
    telemetry={"auto_configure": False},
)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Welcome to AssetDB API", "docs": "/docs"}


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
