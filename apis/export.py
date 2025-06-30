
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, UploadFile, File
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from core.auth import get_current_user
from core.db import DB
from core.wx import search_Biz
from .base import success_response, error_response
from datetime import datetime
from core.config import cfg
from core.res import save_avatar_locally
import pandas as pd
import io
import os
router = APIRouter(prefix=f"/export", tags=["导入/导出"])
@router.get("/mps/export", summary="导出公众号列表")
async def export_mps(
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    kw: str = Query(""),
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        from core.models.feed import Feed
        query = session.query(Feed)
        if kw:
            query = query.filter(Feed.mp_name.ilike(f"%{kw}%"))
        
        mps = query.order_by(Feed.created_at.desc()).limit(limit).offset(offset).all()
        
        # 转换为DataFrame
        data = [{
            "id": mp.id,
            "公众号名称": mp.mp_name,
            "封面图": mp.mp_cover,
            "简介": mp.mp_intro,
            "状态": mp.status,
            "创建时间": mp.created_at.isoformat(),
            "faker_id": mp.faker_id
        } for mp in mps]
        
        df = pd.DataFrame(data)
        
        # 创建临时CSV文件
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
        csv_buffer.seek(0)
        
        # 保存临时文件
        temp_file = "temp_mp_export.csv"
        with open(temp_file, "w", encoding='utf-8-sig') as f:
            f.write(csv_buffer.getvalue())
        
        # 返回文件下载
        return FileResponse(
            temp_file,
            media_type="text/csv",
            filename="公众号列表.csv",
            background=BackgroundTask(lambda: os.remove(temp_file))
        )
        
    except Exception as e:
        print(f"导出公众号列表错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail=error_response(
                code=50001,
                message="导出公众号列表失败"
            )
        )

@router.post("/mps/import", summary="导入公众号列表")
async def import_mps(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        from core.models.feed import Feed
        
        # 读取上传的CSV文件
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents), encoding='utf-8-sig')
        
        # 验证必要字段
        required_columns = ["公众号名称", "封面图", "简介"]
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    code=40001,
                    message=f"CSV文件缺少必要列: {', '.join(missing_cols)}"
                )
            )
        
        # 导入数据
        imported = 0
        updated = 0
        skipped = 0
        
        for _, row in df.iterrows():
            mp_name = row["公众号名称"]
            mp_cover = row["封面图"]
            mp_intro = row.get("简介", "")
            status_val = row.get("状态", 1)
            faker_id = row.get("faker_id", "")
            
            # 检查是否已存在
            existing = session.query(Feed).filter(Feed.mp_name == mp_name).first()
            
            if existing:
                # 更新现有记录
                existing.mp_cover = mp_cover
                existing.mp_intro = mp_intro
                existing.status = status_val
                existing.faker_id = faker_id
                updated += 1
            else:
                # 创建新记录
                mp = Feed(
                    mp_name=mp_name,
                    mp_cover=mp_cover,
                    mp_intro=mp_intro,
                    status=status_val,
                    faker_id=faker_id,
                    created_at=datetime.now()
                )
                session.add(mp)
                imported += 1
        
        session.commit()
        
        return success_response({
            "message": "导入公众号列表成功",
            "stats": {
                "total": len(df),
                "imported": imported,
                "updated": updated,
                "skipped": skipped
            }
        })
        
    except Exception as e:
        session.rollback()
        print(f"导入公众号列表错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail=error_response(
                code=50001,
                message="导入公众号列表失败"
            )
        )