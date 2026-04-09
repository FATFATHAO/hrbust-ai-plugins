import os
import pandas as pd
import boto3
from botocore.client import Config
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pandasai import SmartDataframe
from pandasai.llm.local_llm import LocalLLM
from app.core.config import settings

router = APIRouter(prefix="/excel", tags=["Excel Data Analysis"])

MINIO_ENDPOINT = "http://172.18.0.7:9000"
MINIO_AK = "minioadmin"
MINIO_SK = "minioadmin123"
MINIO_BUCKET = "opencoze"
TEMP_DIR = "/tmp/hrbust_excel_uploads"

os.makedirs(TEMP_DIR, exist_ok=True)


class CozeRequest(BaseModel):
    file: str
    query: str


@router.post("/analyze")
def analyze_excel(payload: CozeRequest):
    try:
        print(f"收到用户指令: {payload.query}")
        print(f"目标Object Key: {payload.file}")

        # S3协议握手
        s3_client = boto3.client(
            "s3",
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_AK,
            aws_secret_access_key=MINIO_SK,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )

        # 重组提取
        temp_file_path = os.path.join(TEMP_DIR, "minio_downloaded.xlsx")
        print(f"正在从金库 {MINIO_BUCKET} 强行提取重组对象...")

        s3_client.download_file(MINIO_BUCKET, payload.file, temp_file_path)
        print(f"对象重组成Excel, 在: {temp_file_path}")

        if payload.file.lower().endswith(".csv"):
            df = pd.read_csv(temp_file_path)
        else:
            df = pd.read_excel(temp_file_path)

        print("PandasAI 原生直连引擎点火...")

        pandasai_llm = LocalLLM(
            api_base="http://172.17.0.1:11434/v1", model="qwen2.5:32b"
        )

        # 强行注入原生引擎
        sdf = SmartDataframe(df, config={"llm": pandasai_llm})
        result = sdf.chat(payload.query)
        print(f"分析结果: {result}")

        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        return {
            "status": "success",
            "query": payload.query,
            "analysis_result": str(result),
        }

    except Exception as e:
        print(f"崩溃: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Excel/CSV文件读取失败: {str(e)}")

