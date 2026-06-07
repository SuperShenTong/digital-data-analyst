from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.router import router as api_router
from app.utils.logger import setup_logger
import uvicorn
import os

logger = setup_logger()

app = FastAPI(title="AI智能数据分析系统", version="1.0.0", description="基于多智能体的企业轻量化智能数据分析平台")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(api_router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def root():
    """返回前端页面"""
    with open(os.path.join(os.path.dirname(__file__), "frontend/index.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)