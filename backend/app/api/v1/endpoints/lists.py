from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_active_user, verify_project_access
from app.models.models import User, Project, List
from app.models.schemas import ListCreate, ListResponse, ListUpdate
from app.core.redis import cache
from app.services.activity_service import log_activity
from datetime import datetime

router = APIRouter()


@router.get("/", response_model=List[ListResponse])
async def get_lists(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取项目的列表"""
    # 验证访问权限
    verify_project_access(project_id, current_user, db)
    
    # 尝试从缓存获取
    cache_key = f"lists:project:{project_id}"
    cached_lists = cache.get(cache_key)
    
    if cached_lists:
        import json
        return json.loads(cached_lists)
    
    # 从数据库获取
    lists = db.query(List).filter(List.project_id == project_id).order_by(List.position).all()
    
    # 缓存结果
    import json
    lists_data = []
    for lst in lists:
        list_dict = {
            "id": lst.id,
            "name": lst.name,
            "position": lst.position,
            "project_id": lst.project_id,
            "created_at": lst.created_at.isoformat(),
            "updated_at": lst.updated_at.isoformat(),
            "cards": []
        }
        lists_data.append(list_dict)
    
    cache.set(cache_key, json.dumps(lists_data), ttl=300)  # 5分钟缓存
    
    return lists


@router.post("/", response_model=ListResponse)
async def create_list(
    project_id: int,
    list_data: ListCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建新列表"""
    # 验证访问权限
    verify_project_access(project_id, current_user, db)
    
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 创建列表
    new_list = List(
        name=list_data.name,
        position=list_data.position,
        project_id=project_id
    )
    
    db.add(new_list)
    db.commit()
    db.refresh(new_list)
    
    # 记录活动
    log_activity(
        db=db,
        user_id=current_user.id,
        action="create",
        entity_type="list",
        entity_id=new_list.id,
        old_values=None,
        new_values={"name": new_list.name, "position": new_list.position}
    )
    
    # 清除缓存
    cache.delete(f"lists:project:{project_id}")
    cache.delete(f"project:{project_id}")
    
    return new_list


@router.get("/{list_id}", response_model=ListResponse)
async def get_list(
    list_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取列表详情"""
    # 获取列表
    lst = db.query(List).filter(List.id == list_id).first()
    if not lst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    # 验证访问权限
    verify_project_access(lst.project_id, current_user, db)
    
    return lst


@router.put("/{list_id}", response_model=ListResponse)
async def update_list(
    list_id: int,
    list_update: ListUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新列表"""
    # 获取列表
    lst = db.query(List).filter(List.id == list_id).first()
    if not lst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    # 验证访问权限
    verify_project_access(lst.project_id, current_user, db)
    
    # 更新列表信息
    update_data = list_update.dict(exclude_unset=True)
    changes = {}
    for field, value in update_data.items():
        if getattr(lst, field) != value:
            changes[field] = {"old": str(getattr(lst, field)), "new": str(value)}
        setattr(lst, field, value)
    
    if changes:
        db.commit()
        db.refresh(lst)
        
        # 记录活动
        log_activity(
            db=db,
            user_id=current_user.id,
            action="update",
            entity_type="list",
            entity_id=lst.id,
            old_values=changes,
            new_values=update_data
        )
    
    # 清除缓存
    cache.delete(f"lists:project:{lst.project_id}")
    cache.delete(f"project:{lst.project_id}")
    
    return lst


@router.delete("/{list_id}")
async def delete_list(
    list_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除列表"""
    # 获取列表
    lst = db.query(List).filter(List.id == list_id).first()
    if not lst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    project_id = lst.project_id
    
    # 验证访问权限
    verify_project_access(project_id, current_user, db)
    
    # 记录删除前的信息
    list_name = lst.name
    
    # 删除列表
    db.delete(lst)
    db.commit()
    
    # 记录活动
    log_activity(
        db=db,
        user_id=current_user.id,
        action="delete",
        entity_type="list",
        entity_id=list_id,
        old_values={"name": list_name, "project_id": project_id},
        new_values=None
    )
    
    # 清除缓存
    cache.delete(f"lists:project:{project_id}")
    cache.delete(f"project:{project_id}")
    
    return {"message": "List deleted successfully"}


@router.post("/{list_id}/move")
async def move_list(
    list_id: int,
    new_position: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """移动列表位置"""
    # 获取列表
    lst = db.query(List).filter(List.id == list_id).first()
    if not lst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    project_id = lst.project_id
    
    # 验证访问权限
    verify_project_access(project_id, current_user, db)
    
    old_position = lst.position
    
    # 更新位置
    lst.position = new_position
    db.commit()
    
    # 记录活动
    log_activity(
        db=db,
        user_id=current_user.id,
        action="move",
        entity_type="list",
        entity_id=lst.id,
        old_values={"position": old_position},
        new_values={"position": new_position}
    )
    
    # 清除缓存
    cache.delete(f"lists:project:{project_id}")
    cache.delete(f"project:{project_id}")
    
    return {"message": "List moved successfully"}