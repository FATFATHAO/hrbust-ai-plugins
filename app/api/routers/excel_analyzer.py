import os
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pandasai import SmartDataframe
from app.core.config import settings

router = APIRouter(prefix="/excel", tags=["Excel Data Analysis"])

MINIO_BASE_DIR = "/data/hrbust-ai-data/hrbust-ai-data-coze/docker/data/minio/opencoze"


# 模型
class CozeRequest(BaseModel):
    file: str
    query: str


@router.post("/analyze")
def analyze_excel(payload: CozeRequest):
    try:
        print(f"收到用户指令: {payload.query}")

        # 物理路径拼接
        # payload.file是类似tos-cn-i-xxx/xxx.xlsx
        base_target_path = os.path.join(MINIO_BASE_DIR, payload.file)
        print(f"锁定MinIO目标: {base_target_path}")

        file_path = base_target_path
        if os.path.isdir(base_target_path):
            print("MinIO数据卷目录！正在执行物理穿透...")
            # 直接锁定里面的真实数据块part.1
            file_path = os.path.join(base_target_path, "part.1")

        # 检查最终的物理数据块到底在不在
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404, detail=f"抱歉，找不到实体数据块！穿透路径: {file_path}"
            )

        print(f"物理实体路径: {file_path}")

        # 本地硬盘直读
        if payload.file.lower().endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        print("PandasAI直读")
        sdf = SmartDataframe(df, config={"llm": settings.local_llm})
        result = sdf.chat(payload.query)
        print(f"分析结果: {result}")

        return {
            "status": "success",
            "query": payload.query,
            "analysis_result": str(result),
        }

    except Exception as e:
        print(f"崩溃: {str(e)}")
        return {"status": "error", "message": f"物理分析引擎发生错误: {str(e)}"}
