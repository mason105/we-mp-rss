from driver.wxarticle import Web
from driver.success import Success
from driver.wx import WX_API
# 示例用法
try:
    urls=[
        "https://mp.weixin.qq.com/s/zmhHRTV2S2ZCr2fYPIg5wA",
        "https://mp.weixin.qq.com/s/SJNb4YfqhlArFdCWhtKmXg"
    ]
    for url in urls:
        Web.Close()
        article_data = Web.get_article_content("https://mp.weixin.qq.com/s/SJNb4YfqhlArFdCWhtKmXg")
        print(article_data)
    Web.Close()
    # WX_API.wxLogin(CallBack=Success)
    # WX_API.Token(CallBack=Success)
    # input("按任意键退出")
except Exception as e:
    print(f"错误: {e}")  