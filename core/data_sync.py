from sqlalchemy import inspect, create_engine, text,String,Text
from sqlalchemy.engine import Engine
from typing import List, Type
from .models.base import Base
from .models.article import Article
from .models.config_management import ConfigManagement
from .models.feed import Feed
from .models.message_task import MessageTask
from .models.user import User
from .models.tags import Tags
def printf(*args):
    if "SYNC" in str(args):
        print(args)
    pass
class ModelSync:
    """模型字段同步到数据库的工具类"""
    
    def _is_utcnow(self, func):
        """检查是否是datetime.utcnow函数"""
        return hasattr(func, '__name__') and func.__name__ == 'utcnow'

    def __init__(self, db_uri: str="sqlite:///db.db",eng:Engine=None):
        """
        初始化同步器
        :param db_uri: 数据库连接URI
        """
        try:
            if eng is  None:
                self.engine: Engine = create_engine(db_uri)
            else:
                self.engine: Engine = eng
            # 测试连接是否有效
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self.models: List[Type[Base]] = [
                Article,
                ConfigManagement,
                Feed,
                MessageTask,
                User,
                Tags
            ]
        except Exception as e:
            import traceback
            error_detail = f"数据库连接失败: {str(e)}\n{traceback.format_exc()}"
            raise ValueError(error_detail)
    
    def sync_all(self, force_update: bool = False) -> None:
        """同步所有模型到数据库
        :param force_update: 是否强制更新字段类型，默认为False
        """
        printf("[SYNC] 开始同步所有模型到数据库...")
        for model in self.models:
            self.sync_model(model, force_update)
        printf("[SYNC] 所有模型同步完成")
    
    def sync_model(self, model: Type[Base], force_update: bool = False) -> None:
        """
        同步单个模型到数据库，兼容SQLite和MySQL
        :param model: 模型类
        :param force_update: 是否强制更新字段类型，默认为False
        """
        try:
            inspector = inspect(self.engine)
            table_name = model.__tablename__
            db_type = self.get_database_type()
            
            printf(f"[SYNC] 开始同步表 {table_name} (数据库类型: {db_type})...")
            
            # 检查表是否存在
            if not inspector.has_table(table_name):
                printf(f"[SYNC] 表 {table_name} 不存在，创建新表")
                with self.engine.begin() as conn:
                    # 自定义表创建逻辑以支持主外键约束
                    table = model.__table__
                    columns = []
                    primary_keys = []
                    foreign_keys = []
                    
                    # 处理列定义
                    for column in table.columns:
                        db_type = self._get_column_type(column)
                        nullable = "NULL" if column.nullable else "NOT NULL"
                        default_value = column.default.arg if column.default is not None else None
                        
                        if callable(default_value):
                            default_value = default_value()
                        
                        column_def = f"{column.name} {db_type} {nullable}"
                        # 设置自动增长属性(仅对INTEGER类型的主键列)
                        if (getattr(column, 'autoincrement', False) and 
                            getattr(column, 'primary_key', False) and
                            str(column.type).upper() in ('INTEGER', 'INT', 'BIGINT')):
                            if db_type == 'mysql':
                                column_def += " AUTO_INCREMENT"
                                printf(f"[SYNC] 为MySQL INTEGER主键列 {column.name} 添加AUTO_INCREMENT")
                            elif db_type == 'sqlite':
                                # SQLite特殊处理: 必须声明为 INTEGER PRIMARY KEY AUTOINCREMENT
                                if "PRIMARY KEY" not in column_def:
                                    column_def += " PRIMARY KEY AUTOINCREMENT"
                                    printf(f"[SYNC] 为SQLite INTEGER主键列 {column.name} 添加PRIMARY KEY AUTOINCREMENT")
                                else:
                                    column_def = column_def.replace("PRIMARY KEY", "PRIMARY KEY AUTOINCREMENT")
                                    printf(f"[SYNC] 为SQLite INTEGER主键列 {column.name} 添加AUTOINCREMENT")
                            elif db_type == 'postgresql':
                                # PostgreSQL使用SERIAL会自动创建序列
                                column_def += " SERIAL"
                                printf(f"[SYNC] 为PostgreSQL INTEGER主键列 {column.name} 添加SERIAL")
                        elif getattr(column, 'autoincrement', False) and getattr(column, 'primary_key', False):
                            printf(f"[WARN] 列 {column.name} 是主键但类型不是INTEGER({str(column.type)})，跳过自动增长属性设置")
            
                        if default_value is not None:
                            column_def += f" DEFAULT '{default_value}'" if isinstance(default_value, str) else f" DEFAULT {default_value}"
                        elif column.nullable:
                            column_def += " DEFAULT NULL"
                        
                        columns.append(column_def)
                        
                        # 收集主键
                        if column.primary_key:
                            primary_keys.append(column.name)
                            
                        # 收集外键
                        if hasattr(column, 'foreign_keys') and column.foreign_keys:
                            for fk in column.foreign_keys:
                                ref_table = fk.column.table.name
                                ref_column = fk.column.name
                                foreign_keys.append(
                                    f"FOREIGN KEY ({column.name}) REFERENCES {ref_table}({ref_column})"
                                )
                    
                    # 构建CREATE TABLE语句
                    create_sql = f"CREATE TABLE {table_name} ("
                    create_sql += ", ".join(columns)
                    
                    # 添加主键约束
                    if primary_keys:
                        create_sql += f", PRIMARY KEY ({', '.join(primary_keys)})"
                    
                    # 添加外键约束
                    if foreign_keys:
                        create_sql += ", " + ", ".join(foreign_keys)
                    
                    create_sql += ")"
                    printf(f"[SQL] 执行表创建SQL:\n{create_sql}")
                    conn.execute(text(create_sql))
                    
                printf(f"[SYNC] 表 {table_name} 创建成功，包含 {len(primary_keys)} 个主键和 {len(foreign_keys)} 个外键")
                return
            
            # 获取数据库表列和模型列
            db_columns = {c['name']: c for c in inspector.get_columns(table_name)}
            model_columns = {c.name: c for c in model.__table__.columns}
            
            # 找出需要添加或修改的列
            for col_name, model_col in model_columns.items():
                if col_name not in db_columns:
                    # 添加新列
                    printf(f"[SYNC] 检测到新列 {col_name}({model_col.type})")
                    self._add_column(table_name, model_col)
                    printf(f"[SYNC] 表 {table_name} 添加列 {col_name} 成功")
                else:
                    # 检查类型是否一致
                    db_col = db_columns[col_name]
                    db_type_str = str(db_col['type'])
                    model_type_str = str(model_col.type)
                    
                    # 检查类型和默认值是否一致
                    if force_update or not self._is_same_type(db_col, model_col):
                        db_default = db_col.get('default')
                        model_default = model_col.default.arg if model_col.default is not None else None
                        if callable(model_default):
                            # 跳过需要上下文的默认值函数
                            if self._is_utcnow(model_default):
                                model_default = None
                            else:
                                model_default = model_default()
                    
                        # 记录差异详情
                        if db_default != model_default:
                            printf(f"[SYNC] 检测到列 {col_name} 默认值差异: 数据库({db_default}) vs 模型({model_default})")
                        if db_col.get('primary_key', False) != model_col.primary_key:
                            printf(f"[SYNC] 检测到列 {col_name} 主键差异: 数据库({db_col.get('primary_key', False)}) vs 模型({model_col.primary_key})")
                        if ('foreign_keys' in db_col) != (hasattr(model_col, 'foreign_keys') and len(model_col.foreign_keys) > 0):
                            printf(f"[SYNC] 检测到列 {col_name} 外键标记差异")
                    
                        printf(f"[SYNC] 检测到列 {col_name} 类型差异: 数据库({db_type_str}) vs 模型({model_type_str})")
                        self._alter_column(table_name, model_col)
                        printf(f"[SYNC] 表 {table_name} 更新列 {col_name} 成功")
                    else:
                        printf(f"[SYNC] 表 {table_name} 列 {col_name} 类型、默认值和约束一致({db_type_str})")
            
            printf(f"[SYNC] 表 {table_name} 同步完成")
        except Exception as e:
            printf(f"[ERROR] 同步表 {table_name} 失败: {str(e)}")
            raise
    
    def get_database_type(self) -> str:
        """获取数据库类型，支持多种常见数据库"""
        try:
            dialect = self.engine.dialect.name
            printf(f"[DEBUG] 检测到数据库方言: {dialect}")
            
            # 支持更多数据库类型
            if dialect == 'sqlite':
                return 'sqlite'
            elif dialect in ('mysql', 'mariadb'):
                return 'mysql'
            elif dialect == 'postgresql':
                return 'postgresql'
            elif dialect == 'oracle':
                return 'oracle'
            elif dialect == 'mssql':
                return 'mssql'
            else:
                printf(f"[WARN] 未知数据库方言: {dialect}, 默认使用mysql兼容模式")
                return 'mysql'
        except Exception as e:
            printf(f"[ERROR] 获取数据库类型失败: {str(e)}")
            return 'mysql'  # 默认回退
    
    def _add_column(self, table_name: str, column) -> None:
        """添加新列到表，支持默认值和外键约束设置，兼容SQLite和MySQL"""
        db_type = self.get_database_type()
        column_type = self._get_column_type(column)
        nullable = "NULL" if column.nullable else "NOT NULL"
        default_value = column.default.arg if column.default is not None else None
        
        # 处理函数默认值
        if callable(default_value):
            # 跳过需要上下文的默认值函数
            if self._is_utcnow(default_value):
                default_value = None
            else:
                default_value = default_value()
        
        with self.engine.begin() as conn:
            try:
                # 构建ADD COLUMN语句
                add_sql = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {column_type} {nullable}"
                
                # 添加自动增长属性(仅对INTEGER类型的主键列)
                if (getattr(column, 'autoincrement', False) and 
                    getattr(column, 'primary_key', False) and
                    str(column.type).upper() in ('INTEGER', 'INT', 'BIGINT')):
                    if db_type == 'mysql':
                        add_sql += " AUTO_INCREMENT"
                        printf(f"[SYNC] 为MySQL INTEGER主键列 {column.name} 添加AUTO_INCREMENT")
                    elif db_type == 'sqlite':
                        # SQLite特殊处理: 必须声明为 INTEGER PRIMARY KEY AUTOINCREMENT
                        if "PRIMARY KEY" not in add_sql:
                            add_sql += " PRIMARY KEY AUTOINCREMENT"
                            printf(f"[SYNC] 为SQLite INTEGER主键列 {column.name} 添加PRIMARY KEY AUTOINCREMENT")
                        else:
                            add_sql = add_sql.replace("PRIMARY KEY", "PRIMARY KEY AUTOINCREMENT")
                            printf(f"[SYNC] 为SQLite INTEGER主键列 {column.name} 添加AUTOINCREMENT")
                    elif db_type == 'postgresql':
                        add_sql += " SERIAL"
                        printf(f"[SYNC] 为PostgreSQL INTEGER主键列 {column.name} 添加SERIAL")
                elif getattr(column, 'autoincrement', False) and getattr(column, 'primary_key', False):
                    printf(f"[WARN] 列 {column.name} 是主键但类型不是INTEGER({str(column.type)})，跳过自动增长属性设置")
                
                # 添加默认值设置
                if default_value is not None:
                    # 根据类型处理默认值格式
                    if isinstance(default_value, str) and not isinstance(column.type, (String, Text)):
                        add_sql += f" DEFAULT {default_value}"
                    else:
                        add_sql += f" DEFAULT '{default_value}'" if isinstance(default_value, str) else f" DEFAULT {default_value}"
                elif column.nullable:
                    add_sql += " DEFAULT NULL"
                
                printf(f"[SQL] 执行添加列SQL:\n{add_sql}")
                conn.execute(text(add_sql))
                
                # 处理外键约束
                if hasattr(column, 'foreign_keys') and column.foreign_keys and db_type != 'sqlite':
                    for fk in column.foreign_keys:
                        ref_table = fk.column.table.name
                        ref_column = fk.column.name
                        fk_sql = (
                            f"ALTER TABLE {table_name} ADD CONSTRAINT fk_{table_name}_{column.name} " +
                            f"FOREIGN KEY ({column.name}) REFERENCES {ref_table}({ref_column})"
                        )
                        printf(f"[DEBUG] 执行外键约束语句: {fk_sql}")
                        conn.execute(text(fk_sql))
            except Exception as e:
                printf(f"[WARN] 添加列 {column.name} 失败: {str(e)}")
                raise
    
    def _alter_column_sqlite(self, table_name: str, column) -> None:
        """SQLite专用: 通过创建新表并复制数据来修改列，支持默认值和自动增长属性"""
        try:
            printf(f"[INFO] 开始修改SQLite表 {table_name} 的列 {column.name}")
            
            with self.engine.begin() as conn:
                # 1. 获取原表结构
                inspector = inspect(self.engine)
                columns = inspector.get_columns(table_name)
                
                # 2. 创建临时表
                temp_table = f"{table_name}_temp"
                conn.execute(text(f"DROP TABLE IF EXISTS {temp_table}"))
                
                # 创建带新结构的临时表，包含默认值和自动增长属性
                column_defs = []
                for col in columns:
                    if col['name'] == column.name:
                        # 处理修改的列
                        col_type = str(column.type)
                        default_value = column.default.arg if column.default is not None else None
                        if callable(default_value):
                            # 跳过需要上下文的默认值函数
                            if self._is_utcnow(default_value):
                                default_value = None
                            else:
                                default_value = default_value()
                        
                        col_def = f"{col['name']} {col_type}"
                        
                        # SQLite特殊处理: AUTOINCREMENT必须与PRIMARY KEY一起声明
                        if (getattr(column, 'autoincrement', False) and 
                            getattr(column, 'primary_key', False) and
                            str(column.type).upper() in ('INTEGER', 'INT', 'BIGINT')):
                            # 确保列定义为 INTEGER PRIMARY KEY AUTOINCREMENT
                            if "PRIMARY KEY" not in col_def:
                                col_def += " PRIMARY KEY AUTOINCREMENT"
                                printf(f"[SYNC] 为SQLite INTEGER主键列 {column.name} 添加PRIMARY KEY AUTOINCREMENT")
                            else:
                                col_def = col_def.replace("PRIMARY KEY", "PRIMARY KEY AUTOINCREMENT")
                                printf(f"[SYNC] 为SQLite INTEGER主键列 {column.name} 添加AUTOINCREMENT")
                        elif getattr(column, 'autoincrement', False) and getattr(column, 'primary_key', False):
                            printf(f"[WARN] 列 {column.name} 是主键但类型不是INTEGER({str(column.type)})，跳过AUTOINCREMENT设置")
                        
                        # 添加默认值设置
                        if default_value is not None:
                            col_def += f" DEFAULT '{default_value}'" if isinstance(default_value, str) else f" DEFAULT {default_value}"
                        elif column.nullable:
                            col_def += " DEFAULT NULL"
                    else:
                        # 保持其他列不变，但保留原列的自动增长属性
                        col_def = f"{col['name']} {col['type']}"
                        if col.get('autoincrement', False) and col.get('primary_key', False):
                            col_def += " AUTOINCREMENT"
                    
                    column_defs.append(col_def)
                
                create_sql = f"CREATE TABLE {temp_table} ({', '.join(column_defs)})"
                printf(f"[SQL] 执行SQLite表重建SQL:\n{create_sql}")
                conn.execute(text(create_sql))
                
                # 3. 复制数据
                copy_sql = f"INSERT INTO {temp_table} SELECT * FROM {table_name}"
                printf(f"[SQL] 执行数据复制SQL:\n{copy_sql}")
                conn.execute(text(copy_sql))
                
                # 4. 删除原表并重命名临时表
                drop_sql = f"DROP TABLE {table_name}"
                rename_sql = f"ALTER TABLE {temp_table} RENAME TO {table_name}"
                printf(f"[SQL] 执行表清理SQL:\n{drop_sql}\n{rename_sql}")
                conn.execute(text(drop_sql))
                conn.execute(text(rename_sql))
                
                printf(f"[INFO] 成功修改SQLite表 {table_name} 的列 {column.name}")
        except Exception as e:
            printf(f"[ERROR] 修改SQLite列 {column.name} 失败: {str(e)}")
            raise
    
    def _alter_column(self, table_name: str, column) -> None:
        """修改表列，支持默认值设置，兼容SQLite和MySQL"""
        db_type = self.get_database_type()
        column_type = self._get_column_type(column)
        nullable = "NULL" if column.nullable else "NOT NULL"
        default_value = column.default.arg if column.default is not None else None
        
        # 处理函数默认值
        if callable(default_value):
            default_value = default_value()
        
        with self.engine.begin() as conn:
            try:
                if db_type == 'sqlite':
                    # SQLite需要特殊处理
                    self._alter_column_sqlite(table_name, column)
                else:
                    # MySQL标准语法
                    # 构建ALTER语句
                    alter_sqls = []
                    
                    # 1. 修改列定义
                    modify_sql = f"ALTER TABLE {table_name} MODIFY COLUMN {column.name} {column_type} {nullable}"
                    
                    # 添加自动增长属性(仅对整数类型的主键列)
                    if (getattr(column, 'autoincrement', False) and 
                        getattr(column, 'primary_key', False) and
                        str(column.type).upper() in ('INTEGER', 'INT', 'BIGINT', 'SMALLINT')):
                        if db_type == 'mysql':
                            modify_sql += " AUTO_INCREMENT"
                            printf(f"[SYNC] 为MySQL INTEGER主键列 {column.name} 添加AUTO_INCREMENT")
                        elif db_type == 'sqlite':
                            modify_sql += " AUTOINCREMENT"
                            printf(f"[SYNC] 为SQLite INTEGER主键列 {column.name} 添加AUTOINCREMENT")
                        elif db_type == 'postgresql':
                            modify_sql += " SERIAL"
                            printf(f"[SYNC] 为PostgreSQL INTEGER主键列 {column.name} 添加SERIAL")
                        else:
                            printf(f"[WARN] 不支持的数据库类型 {db_type} 的自动增长属性")
                        printf(f"[DEBUG] 生成的修改SQL: {modify_sql}")
                    elif getattr(column, 'autoincrement', False) and getattr(column, 'primary_key', False):
                        printf(f"[WARN] 列 {column.name} 是主键但类型不是INTEGER({str(column.type)})，跳过自动增长属性设置")
                    
                    # 添加默认值设置
                    if default_value is not None:
                        # 根据类型处理默认值格式
                        if isinstance(default_value, str) and not isinstance(column.type, (String, Text)):
                            modify_sql += f" DEFAULT {default_value}"
                        else:
                            modify_sql += f" DEFAULT '{default_value}'" if isinstance(default_value, str) else f" DEFAULT {default_value}"
                    elif column.nullable:
                        modify_sql += " DEFAULT NULL"
                    
                    alter_sqls.append(modify_sql)
                    
                    # 2. 处理外键约束
                    if hasattr(column, 'foreign_keys') and column.foreign_keys:
                        # 先删除现有外键约束
                        inspector = inspect(self.engine)
                        for fk in inspector.get_foreign_keys(table_name):
                            if fk['constrained_columns'] == [column.name]:
                                alter_sqls.append(
                                    f"ALTER TABLE {table_name} DROP FOREIGN KEY {fk['name']}"
                                )
                        
                        # 添加新的外键约束
                        for fk in column.foreign_keys:
                            ref_table = fk.column.table.name
                            ref_column = fk.column.name
                            alter_sqls.append(
                                f"ALTER TABLE {table_name} ADD CONSTRAINT fk_{table_name}_{column.name} " +
                                f"FOREIGN KEY ({column.name}) REFERENCES {ref_table}({ref_column})"
                            )
                    
                    # 执行所有ALTER语句
                    for sql in alter_sqls:
                        printf(f"[SQL] 执行修改表SQL:\n{sql}")
                        conn.execute(text(sql))
            except Exception as e:
                printf(f"[WARN] 修改列 {column.name} 失败: {str(e)}")
                raise
    
    def _is_same_type(self, db_col, model_col) -> bool:
        """检查数据库列类型、默认值和约束是否与模型列一致"""
        try:
            db_type = str(db_col['type']).upper()
            model_type = str(model_col.type).upper()
            db_kind = self.get_database_type()
            
            # 去除长度信息(如VARCHAR(255) -> VARCHAR)
            db_base_type = db_type.split('(')[0]
            model_base_type = model_type.split('(')[0]
            
            # 类型映射表
            type_mapping = {
                'sqlite': {
                    'INTEGER': ['INT', 'INTEGER', 'BIGINT', 'SMALLINT'],
                    'TEXT': ['TEXT', 'VARCHAR', 'CHAR', 'STRING', 'NVARCHAR'],
                    'REAL': ['REAL', 'FLOAT', 'DOUBLE', 'DECIMAL'],
                    'BLOB': ['BLOB', 'BINARY', 'VARBINARY'],
                    'NUMERIC': ['NUMERIC', 'DECIMAL']
                },
                'mysql': {
                    'INT': ['INT', 'INTEGER'],
                    'BIGINT': ['BIGINT'],
                    'VARCHAR': ['VARCHAR', 'CHAR', 'NVARCHAR'],
                    'TEXT': ['TEXT', 'LONGTEXT', 'MEDIUMTEXT', 'TINYTEXT', 'MEDIUMTEXT'],
                    'DATETIME': ['DATETIME', 'TIMESTAMP'],
                    'FLOAT': ['FLOAT', 'REAL'],
                    'DOUBLE': ['DOUBLE', 'DOUBLE PRECISION'],
                    'DECIMAL': ['DECIMAL', 'NUMERIC']
                }
            }
            
            # 1. 检查类型是否匹配
            type_match = False
            if db_kind == 'sqlite':
                # SQLite类型系统比较灵活，检查是否属于同一类型组
                for group, types in type_mapping['sqlite'].items():
                    if db_base_type in types and model_base_type in types:
                        printf(f"[DEBUG] 类型匹配: {db_type} 和 {model_type} 都属于 {group} 组")
                        type_match = True
                        break
                if not type_match:
                    printf(f"[DEBUG] 类型不匹配: {db_type} 和 {model_type} 不属于同一组")
                    return False
            else:
                # MySQL需要更精确的类型匹配
                # 忽略长度差异
                if db_base_type != model_base_type:
                    printf(f"[DEBUG] 基础类型不匹配: {db_base_type} != {model_base_type}")
                    return False
                
                # 检查长度是否一致(如果有)
                db_length = db_type.split('(')[1].split(')')[0] if '(' in db_type else None
                model_length = model_type.split('(')[1].split(')')[0] if '(' in model_type else None
                
                if db_length and model_length and db_length != model_length:
                    printf(f"[DEBUG] 类型长度不匹配: {db_length} != {model_length}")
                    return False
            
            # 2. 检查默认值是否匹配
            db_default = db_col.get('default')
            model_default = model_col.default.arg if model_col.default is not None else None
            
            # 处理函数默认值
            if callable(model_default):
                model_default = model_default()
            
            # 比较默认值
            if db_default != model_default:
                printf(f"[DEBUG] 默认值不匹配: 数据库({db_default}) != 模型({model_default})")
                return False
            
            # 3. 检查主键约束是否匹配
            db_primary = db_col.get('primary_key', False)
            model_primary = model_col.primary_key
            if db_primary != model_primary:
                printf(f"[DEBUG] 主键约束不匹配: 数据库({db_primary}) != 模型({model_primary})")
                return False
                
            # 4. 检查外键约束是否匹配
            # 注意: 外键约束通常在表级别定义，这里只检查列是否标记为外键
            db_foreign = 'foreign_keys' in db_col
            model_foreign = hasattr(model_col, 'foreign_keys') and len(model_col.foreign_keys) > 0
            if db_foreign != model_foreign:
                printf(f"[DEBUG] 外键标记不匹配: 数据库({db_foreign}) != 模型({model_foreign})")
                return False
                
            # 5. 检查自动增长属性是否匹配
            db_autoinc = db_col.get('autoincrement', False)
            model_autoinc = getattr(model_col, 'autoincrement', False)
            
            printf(f"[DEBUG] 检查列 {model_col.name} 的自动增长属性: 数据库({db_autoinc}) vs 模型({model_autoinc})")
            
            # 只有当列是主键时才比较自动增长属性
            if db_col.get('primary_key', False) or getattr(model_col, 'primary_key', False):
                printf(f"[DEBUG] 列 {model_col.name} 是主键，检查自动增长属性")
                if db_autoinc != model_autoinc:
                    printf(f"[SYNC] 检测到自动增长属性不匹配: 数据库({db_autoinc}) != 模型({model_autoinc})")
                    printf(f"[SYNC] 列 {model_col.name} 将更新自动增长属性")
                    return False
                else:
                    printf(f"[DEBUG] 自动增长属性匹配: {model_autoinc}")
            else:
                printf(f"[DEBUG] 列 {model_col.name} 不是主键，跳过自动增长属性检查")
                
            return True
        except Exception as e:
            printf(f"[ERROR] 类型/默认值/约束比较失败: {str(e)}")
            return False
    
    def _get_column_type(self, column) -> str:
        """获取SQL列类型字符串，处理数据库差异"""
        db_type = self.get_database_type()
        type_str = str(column.type)
        
        # 调试日志
        printf(f"[DEBUG] 获取列类型: {column.name} - 原始类型: {type_str}")
        if hasattr(column, 'autoincrement'):
            printf(f"[DEBUG] 自动增长属性: {column.autoincrement}")
        if hasattr(column, 'primary_key'):
            printf(f"[DEBUG] 主键属性: {column.primary_key}")
        
        # 处理常见的类型差异
        if db_type == 'sqlite':
            # SQLite类型处理
            if 'VARCHAR' in type_str:
                return 'TEXT'
            elif 'DATETIME' in type_str:
                return 'TEXT'  # SQLite没有专门的DATETIME类型
        elif db_type in ('mysql', 'mariadb'):
            # MySQL/MariaDB类型处理
            if 'MEDIUMTEXT' in type_str:
                return 'MEDIUMTEXT CHARACTER SET utf8mb4'
            elif 'TEXT' in type_str and 'VARCHAR' not in type_str:
                return type_str.replace('TEXT', 'LONGTEXT') + ' CHARACTER SET utf8mb4'
            elif 'VARCHAR' in type_str:
                # 对于主键或索引列，限制VARCHAR长度为191以避免超出MySQL的key长度限制
                if getattr(column, 'primary_key', False) or getattr(column, 'index', False):
                    if 'VARCHAR(255)' in type_str:
                        return 'VARCHAR(191) CHARACTER SET utf8mb4'
                return type_str + ' CHARACTER SET utf8mb4'
                
        return type_str

    # 使用示例
if __name__ == "__main__":
    # 替换为你的数据库连接URI
    db_uri = "sqlite:///data/db.db"
    sync = ModelSync(db_uri)
    sync.sync_all()