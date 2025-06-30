from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime
from core.models.tags import Tags as TagsModel
from core.database import get_db
from sqlalchemy.orm import Session
from schemas.tags import Tags, TagsCreate
from .base import success_response, error_response
from core.auth import get_current_user, requires_permission

# 标签管理API路由
# 提供标签的增删改查功能
# 需要管理员权限执行写操作
router = APIRouter(prefix="/tags", tags=["标签管理"])


@router.get("/", 
    summary="获取标签列表",
    description="分页获取所有标签信息",
    responses={
        200: {
            "description": "成功获取标签列表",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "success",
                        "data": [
                            {
                                "id": "1",
                                "name": "标签1",
                                "cover": "http://example.com/cover1.jpg",
                                "intro": "标签1的描述",
                                "status": 1,
                                "created_at": "2023-01-01T00:00:00",
                                "updated_at": "2023-01-01T00:00:00"
                            }
                        ]
                    }
                }
            }
        }
    })
async def get_tags(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),cur_user: dict = Depends(get_current_user)):
    """
    获取标签列表
    
    参数:
    - skip: 跳过记录数，用于分页
    - limit: 每页记录数，默认100
    
    返回:
    - 包含标签列表的成功响应
    """
    tags = db.query(TagsModel).offset(skip).limit(limit).all()
    return success_response(data=tags)

@router.post("/", response_model=Tags,
    summary="创建新标签",
    description="创建一个新的标签",
    responses={
        200: {
            "description": "成功创建标签",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "success",
                        "data": {
                            "id": "1",
                            "name": "新标签",
                            "cover": "http://example.com/cover.jpg",
                            "intro": "新标签的描述",
                            "status": 1,
                            "created_at": "2023-01-01T00:00:00",
                            "updated_at": "2023-01-01T00:00:00"
                        }
                    }
                }
            }
        },
        500: {
            "description": "服务器内部错误",
            "content": {
                "application/json": {
                    "example": {
                        "code": 500,
                        "message": "Internal server error",
                        "data": None
                    }
                }
            }
        }
    })
async def create_tag(tag: TagsCreate, db: Session = Depends(get_db),cur_user: dict = Depends(get_current_user)):
    """
    创建新标签
    
    参数:
    - tag: TagsCreate模型，包含标签信息
    
    请求体示例:
    {
        "name": "新标签",
        "cover": "http://example.com/cover.jpg",
        "intro": "新标签的描述",
        "status": 1
    }
    
    返回:
    - 成功: 包含新建标签信息的响应
    - 失败: 错误响应
    """
    try:
        db_tag = TagsModel(
            name=tag.name,
            cover=tag.cover,
            intro=tag.intro,
            status=tag.status,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(db_tag)
        db.commit()
        db.refresh(db_tag)
        return success_response(data=db_tag)
    except Exception as e:
        return error_response(code=500, message=str(e))

@router.get("/{tag_id}", response_model=Tags,
    summary="获取单个标签详情",
    description="根据标签ID获取标签详细信息",
    responses={
        200: {
            "description": "成功获取标签详情",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "success",
                        "data": {
                            "id": "1",
                            "name": "标签1",
                            "cover": "http://example.com/cover1.jpg",
                            "intro": "标签1的描述",
                            "status": 1,
                            "created_at": "2023-01-01T00:00:00",
                            "updated_at": "2023-01-01T00:00:00"
                        }
                    }
                }
            }
        },
        404: {
            "description": "标签未找到",
            "content": {
                "application/json": {
                    "example": {
                        "code": 404,
                        "message": "Tag not found",
                        "data": None
                    }
                }
            }
        }
    })
async def get_tag(tag_id: str, db: Session = Depends(get_db),cur_user: dict = Depends(get_current_user)):
    """
    获取单个标签详情
    
    参数:
    - tag_id: 标签ID
    
    返回:
    - 成功: 包含标签详情的响应
    - 失败: 404错误响应(标签不存在)
    """
    tag = db.query(TagsModel).filter(TagsModel.id == tag_id).first()
    if not tag:
        return error_response(code=404, message="Tag not found")
    return success_response(data=tag)

@router.put("/{tag_id}", response_model=Tags, 
    summary="更新标签信息",
    description="根据标签ID更新标签信息",
    responses={
        200: {
            "description": "成功更新标签",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "success",
                        "data": {
                            "id": "1",
                            "name": "更新后的标签",
                            "cover": "http://example.com/new_cover.jpg",
                            "intro": "更新后的描述",
                            "status": 1,
                            "created_at": "2023-01-01T00:00:00",
                            "updated_at": "2023-01-02T00:00:00"
                        }
                    }
                }
            }
        },
        404: {
            "description": "标签未找到",
            "content": {
                "application/json": {
                    "example": {
                        "code": 404,
                        "message": "Tag not found",
                        "data": None
                    }
                }
            }
        },
        500: {
            "description": "服务器内部错误",
            "content": {
                "application/json": {
                    "example": {
                        "code": 500,
                        "message": "Internal server error",
                        "data": None
                    }
                }
            }
        }
    })
async def update_tag(tag_id: str, tag_data: TagsCreate, db: Session = Depends(get_db),cur_user: dict = Depends(get_current_user)):
    """
    更新标签信息
    
    参数:
    - tag_id: 要更新的标签ID
    - tag_data: TagsCreate模型，包含要更新的标签信息
    
    请求体示例:
    {
        "name": "更新后的标签",
        "cover": "http://example.com/new_cover.jpg",
        "intro": "更新后的描述",
        "status": 1
    }
    
    返回:
    - 成功: 包含更新后标签信息的响应
    - 失败: 404错误响应(标签不存在)或500错误响应(服务器错误)
    """
    try:
        tag = db.query(TagsModel).filter(TagsModel.id == tag_id).first()
        if not tag:
            return error_response(code=404, message="Tag not found")
        
        tag.name = tag_data.name
        tag.cover = tag_data.cover
        tag.intro = tag_data.intro
        tag.status = tag_data.status
        tag.updated_at = datetime.now()
        
        db.commit()
        db.refresh(tag)
        return success_response(data=tag)
    except Exception as e:
        return error_response(code=500, message=str(e))

@router.delete("/{tag_id}",
    summary="删除标签",
    description="根据标签ID删除标签",
    responses={
        200: {
            "description": "成功删除标签",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "Tag deleted successfully",
                        "data": None
                    }
                }
            }
        },
        404: {
            "description": "标签未找到",
            "content": {
                "application/json": {
                    "example": {
                        "code": 404,
                        "message": "Tag not found",
                        "data": None
                    }
                }
            }
        },
        500: {
            "description": "服务器内部错误",
            "content": {
                "application/json": {
                    "example": {
                        "code": 500,
                        "message": "Internal server error",
                        "data": None
                    }
                }
            }
        }
    })
async def delete_tag(tag_id: str, db: Session = Depends(get_db),cur_user: dict = Depends(get_current_user)):
    """
    删除标签
    
    参数:
    - tag_id: 要删除的标签ID
    
    返回:
    - 成功: 删除成功的响应
    - 失败: 404错误响应(标签不存在)或500错误响应(服务器错误)
    """
    try:
        tag = db.query(TagsModel).filter(TagsModel.id == tag_id).first()
        if not tag:
            return error_response(code=404, message="Tag not found")
        db.delete(tag)
        db.commit()
        return success_response(message="Tag deleted successfully")
    except Exception as e:
        return error_response(code=500, message=str(e))