from driver.wxarticle import Web
from driver.success import Success
from driver.wx import WX_API
# 示例用法
try:
    article_data = Web.get_article_content("https://mp.weixin.qq.com/s/SJNb4YfqhlArFdCWhtKmXg")
    print(article_data)
    Web.close()
    # WX_API.wxLogin(CallBack=Success)
    # WX_API.Token(CallBack=Success)
    # input("按任意键退出")
except Exception as e:
    print(f"错误: {e}")  