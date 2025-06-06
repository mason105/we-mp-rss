from datetime import datetime, timedelta
import jwt
from functools import wraps
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from passlib.context import CryptContext
from core.models import User as DBUser
from core.db import DB
from core.config import  cfg,API_BASE
# 配置
SECRET_KEY = cfg.get("secret","csol2025")  # 生产环境应使用更安全的密钥
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(cfg.get("token_expire_minutes",30))

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API_BASE}/auth/token",auto_error=False)

def get_user(username: str) -> Optional[DBUser]:
    """从数据库获取用户"""
    session = DB.get_session()
    try:
        return session.query(DBUser).filter(DBUser.username == username).first()
    except Exception as e:
        print(f"获取用户错误: {str(e)}")
        return None

def authenticate_user(username: str, password: str) -> Optional[DBUser]:
    """验证用户凭据"""
    user = get_user(username)
    if not user or not pwd_context.verify(password, user.password_hash):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建JWT Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = get_user(username)
    if user is None:
        raise credentials_exception
        
    return {
        "username": user.username,
        "role": user.role,
        "permissions": user.permissions,
        "original_user": user
    }

def requires_role(role: str):
    """检查用户角色的装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user or current_user.get('role') != role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def requires_permission(permission: str):
    """检查用户权限的装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user or permission not in current_user.get('permissions', []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator
