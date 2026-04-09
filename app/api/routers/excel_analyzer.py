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
        # payload.file 是类似 tos-cn-i-xxx/xxx.xlsx
        base_target_path = os.path.join(MINIO_BASE_DIR, payload.file)
        print(f"锁定MinIO目标: {base_target_path}")

        file_path = base_target_path

        # 👇 极其致命的“深海雷达”穿透逻辑！
        if os.path.isdir(base_target_path):
            print("MinIO数据卷目录，开启扫描...")
            real_data_path = None

            for root, dirs, files in os.walk(base_target_path):
                for f in files:
                    # 只要碰到不是xl.meta的文件（也就是底层的 part.1），是Excel
                    if f != "xl.meta":
                        real_data_path = os.path.join(root, f)
                        break  # 找到了就立刻停止这一层的搜索

                if real_data_path:
                    break  # 找到了就彻底退出整个雷达扫描

            if not real_data_path:
                raise HTTPException(
                    status_code=404, detail="极其惨烈：掘地三尺都没有找到实体数据块！"
                )

            file_path = real_data_path

        # 检查最终的物理数据块到底在不在
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404, detail=f"抱歉，找不到实体数据块！穿透路径: {file_path}"
            )

        print(f"极其完美的物理实体锁定: {file_path}")

        # 本地硬盘直读
        if payload.file.lower().endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path, engine="openpyxl")

        print("PandasAI 直读引擎点火...")
        sdf = SmartDataframe(df, config={"llm": settings.local_llm})
        result = sdf.chat(payload.query)
        print(f"极其完美的分析结果: {result}")

        return {
            "status": "success",
            "query": payload.query,
            "analysis_result": str(result),
        }

    except Exception as e:
        print(f"极其惨烈的崩溃: {str(e)}")
        return {"status": "error", "message": f"物理分析引擎发生错误: {str(e)}"}
