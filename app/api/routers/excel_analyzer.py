import os
import pandas as pd
from pydantic import BaseModel
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from pandasai import SmartDataframe
from app.core.config import settings

# 创建一个独立的路由器，并打上标签
router = APIRouter(prefix="/excel", tags=["Excel Data Analysis"])

UPLOAD_DIR = "/tmp/hrbust_excel_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class CozeRequest(BaseModel):
    file: str  # 这里接收的是Coze的TOS下载链接
    query: str  # 接收用户的自然语言指令


@router.post("/analyze")
async def analyze_excel(file: UploadFile = File(...), query: str = Form(...)):
    try:
        print(f"接到指令: {payload.query}")
        print(f"锁定文件地址: {payload.file}")

        # 从Coze的服务器上把Excel载入本地
        # 给临时文件起个名字
        file_path = os.path.join(UPLOAD_DIR, "temp_coze_download.xlsx")

        # 发起物理下载
        response = requests.get(payload.file)
        if response.status_code != 200:
            raise HTTPException(
                status_code=400, detail="抱歉，无法从Coze存储池下载该表格文件！"
            )

        with open(file_path, "wb") as f:
            f.write(response.content)

        # 用Pandas精准地加载数据
        if payload.file.lower().endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        sdf = SmartDataframe(df, config={"llm": settings.local_llm})
        result = sdf.chat(payload.query)

        if os.path.exists(file_path):
            os.remove(file_path)

        return {
            "status": "success",
            "query": payload.query,
            "analysis_result": str(result),
        }

    except Exception as e:
        print(f"崩溃: {str(e)}")
        return {"status": "error", "message": f"分析引擎发生错误: {str(e)}"}
