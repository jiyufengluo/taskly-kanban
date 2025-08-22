from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_active_user, get_current_superuser
from app.models.models import User
from app.models.schemas import UserResponse, UserUpdate
from app.core.redis import cache

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """获取用户列表（仅超级用户）"""
    # 尝试从缓存获取
    cache_key = f"users:{skip}:{limit}"
    cached_users = cache.get(cache_key)
    
    if cached_users:
        import json
        return json.loads(cached_users)
    
    # 从数据库获取
    users = db.query(User).offset(skip).limit(limit).all()
    
    # 缓存结果
    import json
    from datetime import datetime
    users_data = []
    for user in users:
        user_dict = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "avatar_url": user.avatar_url,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat()
        }
        users_data.append(user_dict)
    
    cache.set(cache_key, json.dumps(users_data), ttl=300)  # 5分钟缓存
    
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户详情"""
    # 用户只能查看自己的详细信息，除非是超级用户
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # 尝试从缓存获取
    cache_key = f"user:{user_id}"
    cached_user = cache.get(cache_key)
    
    if cached_user:
        import json
        user_data = json.loads(cached_user)
        return UserResponse(**user_data)
    
    # 从数据库获取
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 缓存结果
    import json
    user_data = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat()
    }
    cache.set(cache_key, json.dumps(user_data), ttl=300)  # 5分钟缓存
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新用户信息"""
    # 用户只能更新自己的信息，除非是超级用户
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 更新用户信息
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    # 清除缓存
    cache.delete(f"user:{user_id}")
    cache.clear_pattern("users:*")
    
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """删除用户（仅超级用户）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    
    # 清除缓存
    cache.delete(f"user:{user_id}")
    cache.clear_pattern("users:*")
    
    return {"message": "User deleted successfully"}


@router.get("/me/profile", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户个人资料"""
    return current_user