import os
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pandasai import SmartDataframe
from app.core.config import settings

router = APIRouter(prefix=”/excel”, tags=[“Excel Data Analysis”])

MINIO_BASE_DIR = “/data/hrbust-ai-data/hrbust-ai-data-coze/docker/data/minio/opencoze”


class CozeRequest(BaseModel):
    file: str
    query: str


@router.post(“/analyze”)
def analyze_excel(payload: CozeRequest):
    print(f”收到用户指令: {payload.query}”)

    base_target_path = os.path.join(MINIO_BASE_DIR, payload.file)
    print(f”锁定MinIO目标: {base_target_path}”)

    file_path = base_target_path

    if os.path.isdir(base_target_path):
        print(“MinIO数据卷目录，开启扫描...”)
        real_data_path = None

        for root, dirs, files in os.walk(base_target_path):
            for f in files:
                if f != “xl.meta”:
                    real_data_path = os.path.join(root, f)
                    break

            if real_data_path:
                break

        if not real_data_path:
            raise HTTPException(
                status_code=404, detail=”掘地三尺都没有找到实体数据块！”
            )

        file_path = real_data_path

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404, detail=f”找不到实体数据块！穿透路径: {file_path}”
        )

    print(f”物理实体锁定: {file_path}”)

    try:
        if payload.file.lower().endswith(“.csv”):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path, engine=”openpyxl”)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f”Excel/CSV文件读取失败: {str(e)}”)

    try:
        print(“PandasAI 直读引擎点火...”)
        sdf = SmartDataframe(df, config={“llm”: settings.local_llm})
        result = sdf.chat(payload.query)
        print(f”分析结果: {result}”)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f”PandasAI 分析失败: {str(e)}”)

    return {
        “status”: “success”,
        “query”: payload.query,
        “analysis_result”: str(result),
    }
