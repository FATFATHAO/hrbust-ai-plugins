import os
import requests
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pandasai import SmartDataframe
from app.core.config import settings

router = APIRouter(prefix="/excel", tags=["Excel Data Analysis"])

UPLOAD_DIR = "/tmp/hrbust_excel_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class CozeRequest(BaseModel):
    file: str
    query: str


@router.post("/analyze")
def analyze_excel(payload: CozeRequest):
    try:
        print(f"收到用户指令: {payload.query}")
        print(f"收到原始TOS路径: {payload.file}")

        # TOS路径修复
        file_url = payload.file
        # 如果Coze发来的不是完整的http链接, 挂上字节跳动的公网CDN！
        if not file_url.startswith("http"):
            file_url = f"https://lf-bot-studio-plugin-resource.coze.cn/obj/{file_url}"
            print(f"URL修复完成: {file_url}")

        file_path = os.path.join(UPLOAD_DIR, "temp_coze_download.xlsx")
        response = requests.get(file_url)

        if response.status_code != 200:
            raise HTTPException(
                status_code=400, detail=f"下载表格失败！状态码: {response.status_code}"
            )

        with open(file_path, "wb") as f:
            f.write(response.content)
        print("Excel")

        if payload.file.lower().endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        print("PandasAI...")
        sdf = SmartDataframe(df, config={"llm": settings.local_llm})
        result = sdf.chat(payload.query)
        print(f"分析结果: {result}")

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

