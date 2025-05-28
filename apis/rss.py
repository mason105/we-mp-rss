from fastapi import APIRouter, Depends, Query, HTTPException, Request
from fastapi import status
from fastapi.responses import Response
from core.db import DB
from core.rss import RSS
from core.models.feed import Feed
from .base import success_response, error_response
from core.auth import get_current_user

router = APIRouter(prefix="/rss")

@router.get("", summary="获取RSS订阅列表")
async def get_rss_feeds(
    request: Request,
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    # current_user: dict = Depends(get_current_user)
):
    rss = RSS(name="all")
    rss_xml=rss.get_rss()
    if rss_xml is not None:
         return Response(
            content=rss_xml,
            media_type="application/xml"
        )
    session = DB.get_session()
    try:
        total = session.query(Feed).count()
        feeds = session.query(Feed).order_by(Feed.created_at.desc()).limit(limit).offset(offset).all()
        
        # 转换为RSS格式数据
        rss_list = [{
            "id": str(feed.id),
            "title": feed.mp_name,
            "link": f"{request.base_url}rss/{feed.id}",
            "updated": feed.created_at.isoformat()
        } for feed in feeds]
        
        # 生成RSS XML
        rss_xml = rss.generate_rss(rss_list, title="WeRSS订阅")
        
        return Response(
            content=rss_xml,
            media_type="application/xml"
        )
    except Exception as e:
        print(f"获取RSS订阅列表错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(
                code=50001,
                message="获取RSS订阅列表失败"
            )
        )
    finally:
        session.close()

@router.get("/{feed_id}", summary="获取公众号文章RSS")
async def get_mp_articles_rss(
    request: Request,
    feed_id: str,
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    # current_user: dict = Depends(get_current_user)
):
    rss=RSS(name=feed_id)
    rss_xml = rss.get_rss()
    if rss_xml is not None:
         return Response(
            content=rss_xml,
            media_type="application/xml"
        )
    session = DB.get_session()
    try:
        from core.models.article import Article
        
        # 查询公众号信息
        feed = session.query(Feed).filter(Feed.id == feed_id).first()
        if not feed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="公众号不存在"
                )
            )
        
        # 查询文章列表
        total = session.query(Article).filter(Article.mp_id == feed_id).count()
        articles = session.query(Article).filter(Article.mp_id == feed_id)\
            .order_by(Article.publish_time.desc()).limit(limit).offset(offset).all()
        
        # 转换为RSS格式数据
        rss_list = [{
            "id": str(article.id),
            "title": article.title,
            "link": f"https://mp.weixin.qq.com/s/{article.id}",
            "description": article.title,
            "updated": article.updated_at.isoformat()
        } for article in articles]
        
        # 生成RSS XML
        rss_xml = rss.generate_rss(rss_list, title=f"{feed.mp_name}")
        
        return Response(
            content=rss_xml,
            media_type="application/xml"
        )
    except Exception as e:
        print(f"获取公众号文章RSS错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(
                code=50002,
                message="获取公众号文章RSS失败"
            )
        )
    finally:
        session.close()