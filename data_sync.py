import os
import importlib
from typing import Dict, Type
from sqlalchemy import create_engine, MetaData, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import logging

class DatabaseSynchronizer:
    """数据库模型同步器"""
    
    def __init__(self, db_url: str, models_dir: str = "core/models"):
        """
        初始化同步器
        
        :param db_url: 数据库连接URL
        :param models_dir: 模型目录路径
        """
        self.db_url = db_url
        self.models_dir = models_dir
        self.engine = None
        self.models = {}
        
        # 配置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("Sync")
    
    def load_models(self) -> Dict[str, Type[declarative_base()]]:
        """动态加载所有模型类"""
        self.models = {}
        for filename in os.listdir(self.models_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(f"core.models.{module_name}")
                    for name, obj in module.__dict__.items():
                        if isinstance(obj, type) and hasattr(obj, "__tablename__"):
                            self.models[obj.__tablename__] = obj
                    self.logger.info(f"成功加载模型模块: {module_name}")
                except ImportError as e:
                    self.logger.warning(f"无法加载模型模块 {module_name}: {e}")
        return self.models
    
    def _map_types_for_database(self, model):
        """为不同数据库处理特殊类型映射"""
        for column in model.__table__.columns:
            type_str = str(column.type).upper()
            
            # SQLite类型映射
            if "sqlite" in self.db_url:
                # 检查多种可能的MEDIUMTEXT表示形式
                if (hasattr(column.type, "__visit_name__") and column.type.__visit_name__ == "MEDIUMTEXT") or \
                   "MEDIUMTEXT" in type_str or \
                   getattr(column.type, "__class__", None).__name__ == "MEDIUMTEXT":
                    from sqlalchemy import Text
                    column.type = Text()
                    self.logger.debug(f"已将列 {column.name} 的类型从 MEDIUMTEXT 映射为 Text")
            
            # PostgreSQL类型映射
            elif "postgresql" in self.db_url or "postgres" in self.db_url:
                # MEDIUMTEXT映射为TEXT
                if (hasattr(column.type, "__visit_name__") and column.type.__visit_name__ == "MEDIUMTEXT") or \
                   "MEDIUMTEXT" in type_str or \
                   getattr(column.type, "__class__", None).__name__ == "MEDIUMTEXT":
                    from sqlalchemy import Text
                    column.type = Text()
                    self.logger.debug(f"已将列 {column.name} 的类型从 MEDIUMTEXT 映射为 Text")
                
                # LONGTEXT映射为TEXT
                if "LONGTEXT" in type_str or \
                   getattr(column.type, "__class__", None).__name__ == "LONGTEXT":
                    from sqlalchemy import Text
                    column.type = Text()
                    self.logger.debug(f"已将列 {column.name} 的类型从 LONGTEXT 映射为 Text")
                
                # TINYINT映射为SMALLINT
                if "TINYINT" in type_str or \
                   getattr(column.type, "__class__", None).__name__ == "TINYINT":
                    from sqlalchemy import SmallInteger
                    column.type = SmallInteger()
                    self.logger.debug(f"已将列 {column.name} 的类型从 TINYINT 映射为 SmallInteger")
    
    def _check_database_permissions(self):
        """检查数据库权限"""
        try:
            with self.engine.begin() as conn:
                # 检查是否可以创建表
                if "postgresql" in self.db_url or "postgres" in self.db_url:
                    # 检查当前用户权限
                    result = conn.execute("SELECT current_user, current_database(), current_schema()")
                    user_info = result.fetchone()
                    self.logger.info(f"当前用户: {user_info[0]}, 数据库: {user_info[1]}, Schema: {user_info[2]}")
                    
                    # 检查schema权限
                    result = conn.execute("""
                        SELECT has_schema_privilege(current_user, 'public', 'CREATE') as can_create,
                               has_schema_privilege(current_user, 'public', 'USAGE') as can_use
                    """)
                    perms = result.fetchone()
                    
                    if not perms[0]:  # 没有CREATE权限
                        self.logger.error("当前用户没有在public schema中创建表的权限")
                        self.logger.info("请联系数据库管理员执行以下命令:")
                        self.logger.info(f"GRANT CREATE ON SCHEMA public TO {user_info[0]};")
                        return False
                    
                    if not perms[1]:  # 没有USAGE权限
                        self.logger.error("当前用户没有使用public schema的权限")
                        self.logger.info("请联系数据库管理员执行以下命令:")
                        self.logger.info(f"GRANT USAGE ON SCHEMA public TO {user_info[0]};")
                        return False
                        
                return True
        except Exception as e:
            self.logger.warning(f"权限检查失败: {e}")
            return True  # 如果检查失败，继续尝试

    def sync(self):
        """同步模型到数据库"""
        try:
            self.engine = create_engine(self.db_url)
            
            # 检查数据库权限
            if not self._check_database_permissions():
                return False
            
            metadata = MetaData()
            
            # 反射现有数据库结构
            metadata.reflect(bind=self.engine)
            
            # 处理不同数据库的特殊类型映射
            for model in self.models.values():
                self._map_types_for_database(model)
            
            # 加载模型
            if not self.models:
                self.load_models()
                if not self.models:
                    self.logger.error("没有找到任何模型类")
                    return False
            
            # 为不同数据库类型处理自增主键
            if "sqlite" in self.db_url:
                # SQLite使用AUTOINCREMENT
                pass  # SQLAlchemy默认处理
            elif "mysql" in self.db_url:
                # MySQL使用AUTO_INCREMENT
                pass  # SQLAlchemy默认处理
            elif "postgresql" in self.db_url or "postgres" in self.db_url:
                # PostgreSQL使用SERIAL或IDENTITY
                pass  # SQLAlchemy默认处理
            
            # 创建或更新表结构
            for model in self.models.values():
                table_name = model.__tablename__
                inspector = inspect(self.engine)
                
                try:
                    if not inspector.has_table(table_name):
                        # 尝试创建表
                        model.metadata.create_all(self.engine)
                        self.logger.info(f"创建表: {table_name}")
                    else:
                        # 检查字段差异并更新表
                        existing_columns = {c["name"]: c for c in inspector.get_columns(table_name)}
                        model_columns = {c.name: c for c in model.__table__.columns}
                        
                        # 检查新增或修改的字段
                        for col_name, model_col in model_columns.items():
                            if col_name not in existing_columns:
                                # 新增字段 - 根据数据库类型调整语法
                                from sqlalchemy import text
                                try:
                                    with self.engine.begin() as conn:
                                        if "postgresql" in self.db_url or "postgres" in self.db_url:
                                            # PostgreSQL语法
                                            conn.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN "{col_name}" {model_col.type}'))
                                        else:
                                            # SQLite和MySQL语法
                                            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {model_col.type}"))
                                    self.logger.info(f"新增字段: {table_name}.{col_name}")
                                except SQLAlchemyError as e:
                                    self.logger.error(f"添加字段 {table_name}.{col_name} 失败: {e}")
                        
                        self.logger.info(f"表已同步: {table_name}")
                        
                except SQLAlchemyError as e:
                    self.logger.error(f"处理表 {table_name} 时出错: {e}")
                    if "permission denied" in str(e).lower():
                        self.logger.error("权限不足，请检查数据库用户权限")
                        return False
                    continue
            
            self.logger.info("模型同步完成")
            return True
        except SQLAlchemyError as e:
            self.logger.error(f"数据库同步失败: {e}")
            if "permission denied" in str(e).lower():
                self.logger.error("数据库权限不足，请检查以下几点:")
                self.logger.error("1. 确保数据库用户有CREATE权限")
                self.logger.error("2. 确保数据库用户有USAGE权限")
                self.logger.error("3. 如果是PostgreSQL，请联系管理员执行权限授予命令")
            return False
        except Exception as e:
            self.logger.error(f"同步过程中发生未知错误: {e}")
            return False
        finally:
            if self.engine:
                self.engine.dispose()

def main():
    # 示例使用 - 支持多种数据库
    # SQLite
    # synchronizer = DatabaseSynchronizer(db_url="sqlite:///data/db.db")
    
    # PostgreSQL
    # synchronizer = DatabaseSynchronizer(db_url="postgresql://username:password@localhost:5432/dbname")
    
    # MySQL
    # synchronizer = DatabaseSynchronizer(db_url="mysql+pymysql://username:password@localhost:3306/dbname")
    from core.config import cfg
    db_url=cfg.get("db","sqlite:///data/db.db")
    synchronizer = DatabaseSynchronizer(db_url=db_url)
    synchronizer.sync()

if __name__ == "__main__":
    main()