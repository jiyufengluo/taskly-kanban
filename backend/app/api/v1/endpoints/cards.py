from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_active_user, verify_project_access
from app.models.models import User, Project, List, Card, CardLabel, CardAssignment
from app.models.schemas import CardCreate, CardResponse, CardUpdate, CardMoveRequest, CardLabelCreate, CardLabelResponse, CardAssignmentCreate, CardAssignmentResponse
from app.core.redis import cache
from app.services.activity_service import log_activity
from datetime import datetime
import json

router = APIRouter()


@router.get("/", response_model=List[CardResponse])
async def get_cards(
    list_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取列表的卡片"""
    # 验证列表存在和访问权限
    lst = db.query(List).filter(List.id == list_id).first()
    if not lst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    verify_project_access(lst.project_id, current_user, db)
    
    # 尝试从缓存获取
    cache_key = f"cards:list:{list_id}"
    cached_cards = cache.get(cache_key)
    
    if cached_cards:
        return json.loads(cached_cards)
    
    # 从数据库获取
    cards = db.query(Card).filter(Card.list_id == list_id).order_by(Card.position).all()
    
    # 缓存结果
    cards_data = []
    for card in cards:
        card_dict = {
            "id": card.id,
            "title": card.title,
            "description": card.description,
            "position": card.position,
            "due_date": card.due_date.isoformat() if card.due_date else None,
            "list_id": card.list_id,
            "created_at": card.created_at.isoformat(),
            "updated_at": card.updated_at.isoformat(),
            "labels": [],
            "assignments": []
        }
        cards_data.append(card_dict)
    
    cache.set(cache_key, json.dumps(cards_data), ttl=300)  # 5分钟缓存
    
    return cards


@router.post("/", response_model=CardResponse)
async def create_card(
    list_id: int,
    card_data: CardCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建新卡片"""
    # 验证列表存在和访问权限
    lst = db.query(List).filter(List.id == list_id).first()
    if not lst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    verify_project_access(lst.project_id, current_user, db)
    
    # 创建卡片
    new_card = Card(
        title=card_data.title,
        description=card_data.description,
        due_date=card_data.due_date,
        position=card_data.position,
        list_id=list_id
    )
    
    db.add(new_card)
    db.commit()
    db.refresh(new_card)
    
    # 记录活动
    log_activity(
        db=db,
        user_id=current_user.id,
        action="create",
        entity_type="card",
        entity_id=new_card.id,
        old_values=None,
        new_values={"title": new_card.title, "description": new_card.description, "list_id": list_id}
    )
    
    # 清除缓存
    cache.delete(f"cards:list:{list_id}")
    cache.delete(f"lists:project:{lst.project_id}")
    cache.delete(f"project:{lst.project_id}")
    
    return new_card


@router.get("/{card_id}", response_model=CardResponse)
async def get_card(
    card_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取卡片详情"""
    # 获取卡片
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # 验证访问权限
    lst = db.query(List).filter(List.id == card.list_id).first()
    verify_project_access(lst.project_id, current_user, db)
    
    return card


@router.put("/{card_id}", response_model=CardResponse)
async def update_card(
    card_id: int,
    card_update: CardUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新卡片"""
    # 获取卡片
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # 验证访问权限
    lst = db.query(List).filter(List.id == card.list_id).first()
    project_id = lst.project_id
    verify_project_access(project_id, current_user, db)
    
    # 更新卡片信息
    update_data = card_update.dict(exclude_unset=True)
    changes = {}
    for field, value in update_data.items():
        if getattr(card, field) != value:
            changes[field] = {"old": str(getattr(card, field)), "new": str(value)}
        setattr(card, field, value)
    
    if changes:
        db.commit()
        db.refresh(card)
        
        # 记录活动
        log_activity(
            db=db,
            user_id=current_user.id,
            action="update",
            entity_type="card",
            entity_id=card.id,
            old_values=changes,
            new_values=update_data
        )
    
    # 清除缓存
    cache.delete(f"cards:list:{card.list_id}")
    cache.delete(f"lists:project:{project_id}")
    cache.delete(f"project:{project_id}")
    
    return card


@router.delete("/{card_id}")
async def delete_card(
    card_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除卡片"""
    # 获取卡片
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # 验证访问权限
    lst = db.query(List).filter(List.id == card.list_id).first()
    project_id = lst.project_id
    list_id = card.list_id
    
    verify_project_access(project_id, current_user, db)
    
    # 记录删除前的信息
    card_title = card.title
    
    # 删除卡片
    db.delete(card)
    db.commit()
    
    # 记录活动
    log_activity(
        db=db,
        user_id=current_user.id,
        action="delete",
        entity_type="card",
        entity_id=card_id,
        old_values={"title": card_title, "list_id": list_id},
        new_values=None
    )
    
    # 清除缓存
    cache.delete(f"cards:list:{list_id}")
    cache.delete(f"lists:project:{project_id}")
    cache.delete(f"project:{project_id}")
    
    return {"message": "Card deleted successfully"}


@router.post("/move")
async def move_card(
    move_data: CardMoveRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """移动卡片到不同列表"""
    # 验证源列表存在
    source_list = db.query(List).filter(List.id == move_data.source_list_id).first()
    if not source_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source list not found"
        )
    
    # 验证目标列表存在
    target_list = db.query(List).filter(List.id == move_data.target_list_id).first()
    if not target_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target list not found"
        )
    
    # 验证访问权限
    verify_project_access(source_list.project_id, current_user, db)
    verify_project_access(target_list.project_id, current_user, db)
    
    # 获取卡片
    card = db.query(Card).filter(Card.id == move_data.card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # 记录移动前的信息
    old_list_id = card.list_id
    old_position = card.position
    
    # 更新卡片位置和列表
    card.list_id = move_data.target_list_id
    card.position = move_data.new_position
    db.commit()
    
    # 记录活动
    log_activity(
        db=db,
        user_id=current_user.id,
        action="move",
        entity_type="card",
        entity_id=card.id,
        old_values={"list_id": old_list_id, "position": old_position},
        new_values={"list_id": move_data.target_list_id, "position": move_data.new_position}
    )
    
    # 清除缓存
    cache.delete(f"cards:list:{old_list_id}")
    cache.delete(f"cards:list:{move_data.target_list_id}")
    cache.delete(f"lists:project:{source_list.project_id}")
    cache.delete(f"lists:project:{target_list.project_id}")
    cache.delete(f"project:{source_list.project_id}")
    cache.delete(f"project:{target_list.project_id}")
    
    return {"message": "Card moved successfully"}


# 卡片标签管理
@router.post("/{card_id}/labels", response_model=CardLabelResponse)
async def add_card_label(
    card_id: int,
    label_data: CardLabelCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """添加卡片标签"""
    # 验证卡片存在和访问权限
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    lst = db.query(List).filter(List.id == card.list_id).first()
    verify_project_access(lst.project_id, current_user, db)
    
    # 创建标签
    new_label = CardLabel(
        card_id=card_id,
        label=label_data.label,
        color=label_data.color
    )
    
    db.add(new_label)
    db.commit()
    db.refresh(new_label)
    
    # 清除缓存
    cache.delete(f"cards:list:{card.list_id}")
    cache.delete(f"lists:project:{lst.project_id}")
    
    return new_label


@router.delete("/{card_id}/labels/{label_id}")
async def delete_card_label(
    card_id: int,
    label_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除卡片标签"""
    # 验证卡片存在和访问权限
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    lst = db.query(List).filter(List.id == card.list_id).first()
    verify_project_access(lst.project_id, current_user, db)
    
    # 删除标签
    label = db.query(CardLabel).filter(CardLabel.id == label_id, CardLabel.card_id == card_id).first()
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Label not found"
        )
    
    db.delete(label)
    db.commit()
    
    # 清除缓存
    cache.delete(f"cards:list:{card.list_id}")
    cache.delete(f"lists:project:{lst.project_id}")
    
    return {"message": "Label deleted successfully"}


# 卡片分配管理
@router.post("/{card_id}/assignments", response_model=CardAssignmentResponse)
async def assign_card(
    card_id: int,
    assignment_data: CardAssignmentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """分配卡片给用户"""
    # 验证卡片存在和访问权限
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    lst = db.query(List).filter(List.id == card.list_id).first()
    verify_project_access(lst.project_id, current_user, db)
    
    # 验证用户存在
    user = db.query(User).filter(User.id == assignment_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 检查是否已经分配
    existing_assignment = db.query(CardAssignment).filter(
        CardAssignment.card_id == card_id,
        CardAssignment.user_id == assignment_data.user_id
    ).first()
    
    if existing_assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Card already assigned to this user"
        )
    
    # 创建分配
    new_assignment = CardAssignment(
        card_id=card_id,
        user_id=assignment_data.user_id
    )
    
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)
    
    # 清除缓存
    cache.delete(f"cards:list:{card.list_id}")
    cache.delete(f"lists:project:{lst.project_id}")
    
    return new_assignment


@router.delete("/{card_id}/assignments/{assignment_id}")
async def unassign_card(
    card_id: int,
    assignment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """取消卡片分配"""
    # 验证卡片存在和访问权限
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    lst = db.query(List).filter(List.id == card.list_id).first()
    verify_project_access(lst.project_id, current_user, db)
    
    # 删除分配
    assignment = db.query(CardAssignment).filter(CardAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    db.delete(assignment)
    db.commit()
    
    # 清除缓存
    cache.delete(f"cards:list:{card.list_id}")
    cache.delete(f"lists:project:{lst.project_id}")
    
    return {"message": "Assignment removed successfully"}