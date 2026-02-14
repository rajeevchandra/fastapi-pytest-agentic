from fastapi import FastAPI
from .api import router

app = FastAPI(title="FastAPI + Pytest + Agentic Coverage Demo")
app.include_router(router)
