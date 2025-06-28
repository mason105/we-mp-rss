
def sys_notice(text:str="",title:str=""):
    from core.notice import notice
    from core.config import cfg
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

from driver.wx import WX_API
def send_wx_code(title:str="",url:str=""):
    WX_API.GetCode(Notice=CallBackNotice)
    pass
def CallBackNotice():
        url=WX_API.QRcode()['code']
        sys_notice(f"[二维码]：({str(url)})", "微信授权")