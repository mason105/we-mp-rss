import os
from alembic.config import Config
from alembic import command

class DatabaseUpgrader:
    def __init__(self, config_path="alembic.ini"):
        """
        初始化数据库升级器
        :param config_path: alembic配置文件路径
        """
        self.alembic_cfg = Config(config_path)
    
    def upgrade_database(self):
        """执行数据库升级到最新版本"""
        command.upgrade(self.alembic_cfg, "head")
        print("数据库表结构升级完成")
    
    def generate_migration(self, message=None):
        """
        自动生成迁移脚本
        :param message: 可选的迁移信息描述
        """
        command.revision(self.alembic_cfg, autogenerate=True, message=message)
        print("迁移脚本生成完成")

if __name__ == "__main__":
    # 创建升级器实例并执行默认操作
    upgrader = DatabaseUpgrader()
    upgrader.upgrade_database()
    # 如需生成迁移脚本，可取消下面注释
    # upgrader.generate_migration("your migration message here")