import schedule, time
import core.wx as wx 
import core.db as db
from core.config import DEBUG,cfg

import random
import core.log as log
from datetime import datetime

logger=log.logger

# 初始化数据库
wx_db=db.Db()    
wx_db.init(cfg.get("db"))
from core.models.article import Article
def delete_article(id:str):
    try:
        session=wx_db.session
        article = session.query(Article).filter(Article.id == id).first()
        session.delete(article)
        session.commit()
    except Exception as e:
        print(e)
        pass


# 获取公众号列表
mps=wx_db.get_all_mps()

def UpdateArticle(art:dict):
    mps_count=0
    if DEBUG:
        delete_article(art['id'])
        pass
    if  wx_db.add_article(art):
        mps_count=mps_count+1
        return True
    return False

def do_job():
    from core.wx import MpsApi,MpsWeb,WxGather
    print("开始更新")
    wx=WxGather()
    try:
        if cfg.get("model","web")=="web":
            wx=MpsWeb(wx)
        else:
            wx=MpsApi(wx)
        for item in mps:
            try:
                wx.get_Articles(item.faker_id,CallBack=UpdateArticle,Mps_id=item.id,Mps_title=item.mp_name, MaxPage=1)
            except Exception as e:
                print(e)
        print(wx.articles) 
    except Exception as e:
        print(e)         
    finally:
        logger.info(f"所有公众号更新完成,共更新{wx.all_count()}条数据")


def start():
    from core.task import TaskScheduler
    with TaskScheduler() as scheduler:
        # 添加每分钟执行一次的任务
        job_id = scheduler.add_cron_job(do_job, "*/5 * * * *")
        print(f"已添加任务: {job_id}")
        input("按Enter键退出...\n")

def sys_notice(text:str="",title:str=""):
    from core.notice import notice
    markdown_text = f"### {title} 通知\n{text}"
    webhook = cfg.get('notice')['dingding']
    if len(webhook)>0:
        notice(webhook, title, markdown_text)
    feishu_webhook = cfg.get('notice')['feishu']
    if len(feishu_webhook)>0:
        notice(feishu_webhook, title, markdown_text)
    wechat_webhook = cfg.get('notice')['wechat']
    if len(wechat_webhook)>0:
        notice(wechat_webhook, title, markdown_text)



def do_job1():
    print("开始更新")
    all_count=0
    text=f" **时间**：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}\n"
    for item in mps:
        text_list=""
        # 成功更新数量计数
        mps_count=0
        faker_id=item.faker_id
        mp_id=item.id
        print(f'正在更新公众号：{item.mp_name}({item.id})')
            # 获取对应公众号列表
        data=wx.get_list(faker_id,mp_id,0)
        for art in data:
            # 添加到数据库
            if DEBUG:
                delete_article(art['id'])
            if  wx_db.add_article(art):
                mps_count=mps_count+1
                text_list+=f"{mps_count}. [{art['title']}](https://mp.weixin.qq.com/s/{art['id']})[{art['created_at']}]\n"

        logger.info(f"{item.mp_name} 更新结束,共更新{mps_count}")
        text+=f"+ **{item.mp_name}**({mps_count})\n{text_list}"
        all_count=all_count+mps_count

        # 随机休眠 防止被封锁
        # if not cfg.DEBUG:
        #     time.sleep(random.randint(2,5))
    logger.info(f"所有公众号更新完成,共更新{all_count}条数据")
    text+=f"\n所有公众号更新完成,共更新{all_count}条数据"
    if all_count>0:
        sys_notice(text,cfg.get('app_name',default='we-mp-rss'))
    else:
        print(text)    

if __name__ == '__main__':
    do_job()