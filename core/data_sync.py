from typing import Dict, List, Optional
from datetime import datetime
import logging
from sqlalchemy import inspect
from core.db import Db
from core.models.base import Base
from core.print import print_info, print_error
from core.log import logger

class DataSync:
    def __init__(self, source_db: Db, target_db: Db):
        self.source_db = source_db
        self.target_db = target_db
        
    def sync_model_to_table(self, model_class):
        """将模型类同步到数据库表结构"""
        try:
            # 检查表是否已存在
            if not inspect(self.target_db.engine).has_table(model_class.__tablename__):
                # 表不存在则创建
                model_class.__table__.create(self.target_db.engine)
                logger.info(f"Created table {model_class.__tablename__}")
                return True
            
            # 表已存在则比较差异
            temp_table = type(f"Temp{model_class.__name__}", (Base,), {
                '__tablename__': f"temp_{model_class.__tablename__}",
                '__table_args__': {'extend_existing': True}
            })
            
            # 复制列定义
            for col in model_class.__table__.columns:
                temp_table.__table__.append_column(col.copy())
                
            # 生成并执行DDL
            ddl_statements = self.generate_ddl(model_class, temp_table)
            if ddl_statements:
                logger.info(f"Updating table {model_class.__tablename__} with {len(ddl_statements)} changes")
                return self.execute_ddl(ddl_statements)
            
            logger.info(f"Table {model_class.__tablename__} is already up to date")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync model {model_class.__name__} to table: {e}")
            # raise e
            return False
        
    def compare_schemas(self, source_table, target_table):
        """比较两个表的结构差异"""
        source_columns = {c.name: c.type for c in source_table.__table__.columns}
        target_columns = {c.name: c.type for c in target_table.__table__.columns}
        
        # 找出新增、修改和删除的列
        added = {k: v for k, v in source_columns.items() if k not in target_columns}
        changed = {
            k: (v, target_columns[k])
            for k, v in source_columns.items()
            if k in target_columns and v != target_columns[k]
        }
        removed = {k: v for k, v in target_columns.items() if k not in source_columns}
        
        return {
            'added_columns': added,
            'changed_columns': changed,
            'removed_columns': removed
        }
        
    def generate_ddl(self, source_table, target_table):
        """根据表结构差异生成DDL语句"""
        diff = self.compare_schemas(source_table, target_table)
        ddl_statements = []
        
        # 获取数据库方言
        dialect = self.target_db.engine.dialect.name
        
        # 处理新增列
        for column_name, column_type in diff['added_columns'].items():
            ddl_statements.append(
                f"ALTER TABLE {target_table.__tablename__} ADD COLUMN {column_name} {column_type}"
            )
        
        # 处理修改列
        for column_name, (source_type, target_type) in diff['changed_columns'].items():
            if dialect == 'sqlite':
                # SQLite不支持直接修改列类型，需要创建新表并复制数据
                ddl_statements.extend([
                    f"ALTER TABLE {target_table.__tablename__} RENAME TO {target_table.__tablename__}_old",
                    f"CREATE TABLE {target_table.__tablename__} AS SELECT * FROM {target_table.__tablename__}_old",
                    f"DROP TABLE {target_table.__tablename__}_old"
                ])
            else:
                # MySQL/PostgreSQL等支持ALTER COLUMN TYPE
                ddl_statements.append(
                    f"ALTER TABLE {target_table.__tablename__} ALTER COLUMN {column_name} TYPE {source_type}"
                )
        
        # 处理删除列
        for column_name in diff['removed_columns'].keys():
            if dialect == 'sqlite':
                # SQLite不支持直接删除列，需要创建新表并复制数据
                ddl_statements.extend([
                    f"ALTER TABLE {target_table.__tablename__} RENAME TO {target_table.__tablename__}_old",
                    f"CREATE TABLE {target_table.__tablename__} AS SELECT * FROM {target_table.__tablename__}_old WHERE 1=0",
                    f"INSERT INTO {target_table.__tablename__} SELECT * FROM {target_table.__tablename__}_old",
                    f"DROP TABLE {target_table.__tablename__}_old"
                ])
            else:
                ddl_statements.append(
                    f"ALTER TABLE {target_table.__tablename__} DROP COLUMN {column_name}"
                )
        
        return ddl_statements
        
    def execute_ddl(self, ddl_statements):
        """执行DDL语句"""
        try:
            for stmt in ddl_statements:
                self.target_db.engine.execute(stmt)
            return True
        except Exception as e:
            logger.error(f"DDL execution failed: {e}")
            return False
        
    def map_schema(self, source_schema: Dict, target_schema: Dict) -> Dict:
        """定义源和目标数据结构的映射关系"""
        return {
            source_field: target_field
            for source_field, target_field in zip(source_schema.keys(), target_schema.keys())
        }
        
    def transform_data(self, source_data: Dict, mapping: Dict) -> Dict:
        """根据映射关系转换数据"""
        return {
            target_field: source_data[source_field]
            for source_field, target_field in mapping.items()
        }
        
    def validate_data(self, data: Dict, schema: Dict) -> bool:
        """验证数据是否符合目标结构"""
        return all(field in data for field in schema.keys())
        
    def full_sync(self, source_table: str, target_table: str, batch_size: int = 100) -> bool:
        """全量数据同步"""
        try:
            offset = 0
            total_processed = 0
            logger.info(f"Starting full sync from {source_table.__tablename__} to {target_table.__tablename__}")
            
            while True:
                source_data = self.source_db.session.query(source_table).limit(batch_size).offset(offset).all()
                if not source_data:
                    break
                batch_count = 0
                for data in source_data:
                    try:
                        transformed = self.transform_data(data.__dict__, self.map_schema(
                            source_table.__table__.columns,
                            target_table.__table__.columns
                        ))
                        
                        if self.validate_data(transformed, target_table.__table__.columns):
                            self.target_db.session.add(target_table(**transformed))
                            batch_count += 1
                            total_processed += 1
                            
                        if batch_count % 10 == 0:  # 每10条记录打印一次进度
                            logger.info(f"Processed {total_processed} records")
                            
                    except Exception as e:
                        logger.error(f"Error processing record {data.id}: {e}")
                        continue
                    
                    if self.validate_data(transformed, target_table.__table__.columns):
                        self.db.session.add(target_table(**transformed))
                        
                offset += batch_size
                try:
                    self.target_db.session.commit()
                    logger.info(f"Successfully committed batch {offset//batch_size}")
                except Exception as e:
                    logger.error(f"Batch commit failed: {e}")
                    self.target_db.session.rollback()
                    
            logger.info(f"Full sync completed. Total records processed: {total_processed}")
            return True
            
        except Exception as e:
            logger.error(f"Full sync failed: {e}")
            self.target_db.session.rollback()
            return False
            
    def incremental_sync(self, source_table: str, target_table: str, since: datetime) -> bool:
        """增量数据同步"""
        try:
            source_data = self.source_db.session.query(source_table).filter(
                source_table.updated_at >= since
            ).all()
            
            for data in source_data:
                transformed = self.transform_data(data.__dict__, self.map_schema(
                    source_table.__table__.columns,
                    target_table.__table__.columns
                ))
                
                if self.validate_data(transformed, target_table.__table__.columns):
                    self.target_db.session.merge(target_table(**transformed))
                    
            self.target_db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Incremental sync failed: {e}")
            self.target_db.session.rollback()
            return False