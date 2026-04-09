from fastapi import FastAPI
from app.api.routers import excel_analyzer
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# 将Excel插件路由挂载到/api/v1目录下
app.include_router(excel_analyzer.router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "200", "service": "AI Tooling Microservice"}
