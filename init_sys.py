from core.models.user import User
from core.models.article import Article
from core.models.config_management import ConfigManagement
from core.models.feed import Feed
from core.models.message_task import MessageTask
import core.db as db
from core.config import cfg
from core.auth import pwd_context
from core.data_sync import DataSync
import time
import os
def init_user():
    try:
      username,password=os.getenv("USERNAME", "admin"),os.getenv("PASSWORD", "admin@888")
      db.DB.create_tables()
      
     
      db.DB.session.add(User(
          id=0,
          username=username,
          password_hash=pwd_context.hash(password),
          ))
      db.DB.session.commit()
    except Exception as e:
        print(f"Init error: {str(e)}")
def sync_models():
     # 同步模型到表结构
      data_sync = DataSync(db.DB, db.DB)
      models = [User, Article, ConfigManagement, Feed, MessageTask]
      for model in models:
          if not data_sync.sync_model_to_table(model):
              print(f"Failed to sync model {model.__name__} to table")
          else:
              print(f"Successfully synced model {model.__name__} to table")
def init():
    sync_models()
    init_user()

if __name__ == '__main__':
    init()