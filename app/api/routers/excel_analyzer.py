import os
import pandas as pd
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from pandasai import SmartDataframe
from app.core.config import settings

# 创建一个独立的路由器，并打上标签
router = APIRouter(prefix="/excel", tags=["Excel Data Analysis"])

UPLOAD_DIR = "/tmp/hrbust_excel_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/analyze")
async def analyze_excel(
    file: UploadFile = File(...), 
    query: str = Form(...)
):
    try:
        # 文件保存逻辑
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # 数据加载
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            raise HTTPException(status_code=400, detail="极其抱歉，仅支持 CSV/Excel")

        # core层调用全局LLM
        sdf = SmartDataframe(df, config={"llm": settings.local_llm})
        result = sdf.chat(query)
        
        os.remove(file_path) 

        return JSONResponse(content={
            "status": "success",
            "query": query,
            "analysis_result": str(result)
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={
            "status": "error",
            "message": str(e)
        })
