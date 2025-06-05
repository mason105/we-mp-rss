from core.models.message_task import MessageTask
from core.models.feed import Feed
from core.models.article import Article
from .notice import sys_notice

class MessageWebHook():
    task: MessageTask
    feed:Feed
    articles:list=[Article]
    pass
def web_hook(hook:MessageWebHook):
    print(hook)
