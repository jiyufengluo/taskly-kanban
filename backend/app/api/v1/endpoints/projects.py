from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_active_user, verify_project_access
from app.models.models import User, Project, List, Card, ProjectMember
from app.models.schemas import ProjectCreate, ProjectResponse, ProjectUpdate, ProjectMemberCreate, ProjectMemberResponse
from app.core.redis import cache
from app.services.activity_service import log_activity
from datetime import datetime

router = APIRouter()


@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户的项目列表"""
    # 尝试从缓存获取
    cache_key = f"projects:user:{current_user.id}:{skip}:{limit}"
    cached_projects = cache.get(cache_key)
    
    if cached_projects:
        import json
        return json.loads(cached_projects)
    
    # 从数据库获取用户有权限的项目
    projects = db.query(Project).join(ProjectMember).filter(
        (Project.owner_id == current_user.id) | 
        (ProjectMember.user_id == current_user.id)
    ).offset(skip).limit(limit).all()
    
    # 缓存结果
    import json
    projects_data = []
    for project in projects:
        project_dict = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "owner_id": project.owner_id,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
            "owner": {
                "id": project.owner.id,
                "email": project.owner.email,
                "username": project.owner.username,
                "full_name": project.owner.full_name,
                "avatar_url": project.owner.avatar_url,
                "created_at": project.owner.created_at.isoformat(),
                "updated_at": project.owner.updated_at.isoformat()
            },
            "members": []
        }
        projects_data.append(project_dict)
    
    cache.set(cache_key, json.dumps(projects_data), ttl=300)  # 5分钟缓存
    
    return projects


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建新项目"""
    # 创建项目
    new_project = Project(
        name=project_data.name,
        description=project_data.description,
        owner_id=current_user.id
    )
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    # 创建项目所有者成员记录
    owner_member = ProjectMember(
        project_id=new_project.id,
        user_id=current_user.id,
        role='owner'
    )
    db.add(owner_member)
    
    # 创建默认列表
    default_lists = [
        {"name": "待办", "position": 0},
        {"name": "进行中", "position": 1},
        {"name": "已完成", "position": 2}
    ]
    
    for list_data in default_lists:
        new_list = List(
            name=list_data["name"],
            position=list_data["position"],
            project_id=new_project.id
        )
        db.add(new_list)
    
    db.commit()
    
    # 记录活动
    log_activity(
        db=db,
        user_id=current_user.id,
        action="create",
        entity_type="project",
        entity_id=new_project.id,
        old_values=None,
        new_values={"name": new_project.name, "description": new_project.description}
    )
    
    # 清除缓存
    cache.clear_pattern(f"projects:user:{current_user.id}:*")
    
    return new_project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取项目详情"""
    # 验证访问权限
    verify_project_access(project_id, current_user, db)
    
    # 尝试从缓存获取
    cache_key = f"project:{project_id}"
    cached_project = cache.get(cache_key)
    
    if cached_project:
        import json
        project_data = json.loads(cached_project)
        return ProjectResponse(**project_data)
    
    # 从数据库获取
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 获取项目成员
    members = db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()
    
    # 缓存结果
    import json
    project_data = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "owner_id": project.owner_id,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
        "owner": {
            "id": project.owner.id,
            "email": project.owner.email,
            "username": project.owner.username,
            "full_name": project.owner.full_name,
            "avatar_url": project.owner.avatar_url,
            "created_at": project.owner.created_at.isoformat(),
            "updated_at": project.owner.updated_at.isoformat()
        },
        "members": []
    }
    
    for member in members:
        member_data = {
            "id": member.id,
            "project_id": member.project_id,
            "user_id": member.user_id,
            "role": member.role,
            "joined_at": member.joined_at.isoformat(),
            "user": {
                "id": member.user.id,
                "email": member.user.email,
                "username": member.user.username,
                "full_name": member.user.full_name,
                "avatar_url": member.user.avatar_url,
                "created_at": member.user.created_at.isoformat(),
                "updated_at": member.user.updated_at.isoformat()
            }
        }
        project_data["members"].append(member_data)
    
    cache.set(cache_key, json.dumps(project_data), ttl=300)  # 5分钟缓存
    
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新项目"""
    # 验证访问权限
    verify_project_access(project_id, current_user, db)
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 只有项目所有者可以更新项目
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can update the project"
        )
    
    # 更新项目信息
    update_data = project_update.dict(exclude_unset=True)
    changes = {}
    for field, value in update_data.items():
        if getattr(project, field) != value:
            changes[field] = {"old": str(getattr(project, field)), "new": str(value)}
        setattr(project, field, value)
    
    if changes:
        db.commit()
        db.refresh(project)
        
        # 记录活动
        log_activity(
            db=db,
            user_id=current_user.id,
            action="update",
            entity_type="project",
            entity_id=project.id,
            old_values=changes,
            new_values=update_data
        )
    
    # 清除缓存
    cache.delete(f"project:{project_id}")
    cache.clear_pattern(f"projects:user:{current_user.id}:*")
    
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除项目"""
    # 验证访问权限
    verify_project_access(project_id, current_user, db)
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 只有项目所有者可以删除项目
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can delete the project"
        )
    
    project_name = project.name
    db.delete(project)
    db.commit()
    
    # 记录活动
    log_activity(
        db=db,
        user_id=current_user.id,
        action="delete",
        entity_type="project",
        entity_id=project_id,
        old_values={"name": project_name},
        new_values=None
    )
    
    # 清除缓存
    cache.delete(f"project:{project_id}")
    cache.clear_pattern(f"projects:user:{current_user.id}:*")
    
    return {"message": "Project deleted successfully"}


@router.post("/{project_id}/members", response_model=ProjectMemberResponse)
async def add_project_member(
    project_id: int,
    member_data: ProjectMemberCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """添加项目成员"""
    # 验证访问权限
    verify_project_access(project_id, current_user, db)
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 只有项目所有者可以添加成员
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can add members"
        )
    
    # 检查用户是否存在
    user = db.query(User).filter(User.id == member_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 检查用户是否已经是成员
    existing_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == member_data.user_id
    ).first()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a project member"
        )
    
    # 添加成员
    new_member = ProjectMember(
        project_id=project_id,
        user_id=member_data.user_id,
        role=member_data.role
    )
    
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    
    # 记录活动
    log_activity(
        db=db,
        user_id=current_user.id,
        action="create",
        entity_type="assignment",
        entity_id=new_member.id,
        old_values=None,
        new_values={"project_id": project_id, "user_id": member_data.user_id, "role": member_data.role}
    )
    
    # 清除缓存
    cache.delete(f"project:{project_id}")
    cache.clear_pattern(f"projects:user:{current_user.id}:*")
    
    return new_member


@router.delete("/{project_id}/members/{user_id}")
async def remove_project_member(
    project_id: int,
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """移除项目成员"""
    # 验证访问权限
    verify_project_access(project_id, current_user, db)
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 只有项目所有者可以移除成员
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can remove members"
        )
    
    # 查找成员记录
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # 不能移除项目所有者
    if user_id == project.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove project owner"
        )
    
    # 移除成员
    db.delete(member)
    db.commit()
    
    # 记录活动
    log_activity(
        db=db,
        user_id=current_user.id,
        action="delete",
        entity_type="assignment",
        entity_id=member.id,
        old_values={"project_id": project_id, "user_id": user_id, "role": member.role},
        new_values=None
    )
    
    # 清除缓存
    cache.delete(f"project:{project_id}")
    cache.clear_pattern(f"projects:user:{current_user.id}:*")
    
    return {"message": "Member removed successfully"}