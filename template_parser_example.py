"""
模板引擎使用示例

基础用法:
1. 简单变量替换: {{variable}}
2. 条件判断: {% if condition %}...{% endif %}
3. 循环结构: {% for item in items %}...{% endfor %}
"""

from core.lax import TemplateParser


from core.models import Feed, Article
from core.db import DB
# 示例4: 使用Feed和Article模型数据
feed_template = """
### {{feed.mp_name}} 订阅消息：
{% if articles %}
{% for article in articles %}
- [**{{ article.title }}**]({{article.url}}) ({{ article.publish_time }})\n
{% endfor %}
{% else %}
- 暂无文章\n
{% endif %}
"""

# 从数据库获取真实Feed和Article数据
session = DB.get_session()
from datetime import datetime
feed = session.query(Feed).first()
articles = session.query(Article).order_by(Article.publish_time.desc()).limit(5).all()
context4 = {
    "feed": {
        "mp_name": feed.mp_name,
        "mp_intro": feed.mp_intro
    },
    "articles": [
        {
            "title": article.title,
            "url": f"{article.url}",
            "publish_time": datetime.strftime(datetime.fromtimestamp(article.publish_time), "%Y/%m/%d %H:%M")
        } for article in articles
    ]
}
print("示例4数据:", context4)
parser4 = TemplateParser(feed_template)
result4 = parser4.render(context4)
print(result4)
from core.notice import notice
from core.config import cfg
notice(webhook_url=cfg.get("notice.dingding"),title="订阅消息",text=result4)