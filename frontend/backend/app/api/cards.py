from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models import User, Project, Board, List as BoardList, Card, ProjectMember
from app.schemas import (
    Card as CardSchema,
    CardCreate,
    CardUpdate,
    CardMove,
    CardPositionUpdate,
    CardAssignment
)

router = APIRouter()

def check_card_access(card_id: int, user_id: int, db: Session):
    """检查用户是否有卡片访问权限"""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # 通过卡片->列表->看板->项目检查权限
    list_obj = db.query(BoardList).filter(BoardList.id == card.list_id).first()
    board = db.query(Board).filter(Board.id == list_obj.board_id).first()
    
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == board.project_id,
        ProjectMember.user_id == user_id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this card"
        )
    
    return card, list_obj, board

def check_list_access(list_id: int, user_id: int, db: Session):
    """检查用户是否有列表访问权限"""
    list_obj = db.query(BoardList).filter(BoardList.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    board = db.query(Board).filter(Board.id == list_obj.board_id).first()
    
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == board.project_id,
        ProjectMember.user_id == user_id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this list"
        )
    
    return list_obj, board

@router.post("/", response_model=CardSchema, status_code=status.HTTP_201_CREATED)
def create_card(
    card: CardCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建新卡片"""
    # 检查列表访问权限
    list_obj, board = check_list_access(card.list_id, current_user.id, db)
    
    # 如果没有指定位置，设置为列表中的最后一个位置
    if card.position == 0:
        max_position = db.query(Card).filter(
            Card.list_id == card.list_id
        ).count()
        card.position = max_position
    
    # 如果指定了assignee_id，检查该用户是否是项目成员
    if card.assignee_id:
        assignee_member = db.query(ProjectMember).filter(
            ProjectMember.project_id == board.project_id,
            ProjectMember.user_id == card.assignee_id
        ).first()
        
        if not assignee_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee is not a member of this project"
            )
    
    db_card = Card(
        title=card.title,
        description=card.description,
        position=card.position,
        priority=card.priority,
        due_date=card.due_date,
        list_id=card.list_id,
        creator_id=current_user.id,
        assignee_id=card.assignee_id
    )
    
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    
    # 触发WebSocket通知
    from app.api.websocket import notifier
    import asyncio
    
    # 准备卡片数据用于WebSocket通知
    card_data = {
        "id": db_card.id,
        "title": db_card.title,
        "description": db_card.description,
        "position": db_card.position,
        "list_id": db_card.list_id,
        "creator_id": db_card.creator_id,
        "assignee_id": db_card.assignee_id,
        "due_date": db_card.due_date.isoformat() if db_card.due_date else None
    }
    
    # 异步发送WebSocket通知
    try:
        asyncio.create_task(
            notifier.notify_card_created(board.project_id, card_data, current_user.id)
        )
    except Exception as e:
        print(f"WebSocket notification error: {e}")
    
    return db_card

@router.get("/list/{list_id}", response_model=List[CardSchema])
def read_list_cards(
    list_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取列表中的所有卡片"""
    # 检查列表访问权限
    check_list_access(list_id, current_user.id, db)
    
    cards = db.query(Card).filter(
        Card.list_id == list_id
    ).order_by(Card.position).all()
    
    return cards

@router.get("/{card_id}", response_model=CardSchema)
def read_card(
    card_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取卡片详情"""
    card, _, _ = check_card_access(card_id, current_user.id, db)
    return card

@router.put("/{card_id}", response_model=CardSchema)
def update_card(
    card_id: int,
    card_update: CardUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新卡片信息"""
    card, list_obj, board = check_card_access(card_id, current_user.id, db)
    
    # 如果更新了assignee_id，检查该用户是否是项目成员
    if card_update.assignee_id is not None:
        if card_update.assignee_id != 0:  # 0表示取消分配
            assignee_member = db.query(ProjectMember).filter(
                ProjectMember.project_id == board.project_id,
                ProjectMember.user_id == card_update.assignee_id
            ).first()
            
            if not assignee_member:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assignee is not a member of this project"
                )
        else:
            card_update.assignee_id = None
    
    # 更新卡片信息
    update_data = card_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(card, field, value)
    
    db.commit()
    db.refresh(card)
    
    return card

@router.put("/{card_id}/move", response_model=CardSchema)
def move_card(
    card_id: int,
    card_move: CardMove,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """移动卡片到不同列表或位置"""
    card, old_list, old_board = check_card_access(card_id, current_user.id, db)
    
    # 检查目标列表访问权限
    new_list, new_board = check_list_access(card_move.list_id, current_user.id, db)
    
    # 确保新旧列表在同一个项目中
    if old_board.project_id != new_board.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot move card between different projects"
        )
    
    old_list_id = card.list_id
    old_position = card.position
    new_list_id = card_move.list_id
    new_position = card_move.position
    
    if old_list_id == new_list_id:
        # 在同一列表内移动
        if new_position > old_position:
            # 向后移动，其他卡片向前移动
            db.query(Card).filter(
                Card.list_id == old_list_id,
                Card.position > old_position,
                Card.position <= new_position,
                Card.id != card_id
            ).update({Card.position: Card.position - 1})
        elif new_position < old_position:
            # 向前移动，其他卡片向后移动
            db.query(Card).filter(
                Card.list_id == old_list_id,
                Card.position >= new_position,
                Card.position < old_position,
                Card.id != card_id
            ).update({Card.position: Card.position + 1})
    else:
        # 移动到不同列表
        # 更新原列表中的卡片位置
        db.query(Card).filter(
            Card.list_id == old_list_id,
            Card.position > old_position
        ).update({Card.position: Card.position - 1})
        
        # 更新目标列表中的卡片位置
        db.query(Card).filter(
            Card.list_id == new_list_id,
            Card.position >= new_position
        ).update({Card.position: Card.position + 1})
    
    # 更新卡片的列表和位置
    card.list_id = new_list_id
    card.position = new_position
    
    db.commit()
    db.refresh(card)
    
    return card

@router.put("/{card_id}/position", response_model=CardSchema)
def update_card_position(
    card_id: int,
    position_update: CardPositionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新卡片在当前列表中的位置"""
    card, list_obj, board = check_card_access(card_id, current_user.id, db)
    
    old_position = card.position
    new_position = position_update.position
    
    # 更新其他卡片的位置
    if new_position > old_position:
        # 向后移动，其他卡片向前移动
        db.query(Card).filter(
            Card.list_id == card.list_id,
            Card.position > old_position,
            Card.position <= new_position,
            Card.id != card_id
        ).update({Card.position: Card.position - 1})
    elif new_position < old_position:
        # 向前移动，其他卡片向后移动
        db.query(Card).filter(
            Card.list_id == card.list_id,
            Card.position >= new_position,
            Card.position < old_position,
            Card.id != card_id
        ).update({Card.position: Card.position + 1})
    
    # 更新当前卡片位置
    card.position = new_position
    
    db.commit()
    db.refresh(card)
    
    return card

@router.put("/{card_id}/assign", response_model=CardSchema)
def assign_card(
    card_id: int,
    assignment: CardAssignment,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """分配卡片给用户"""
    card, list_obj, board = check_card_access(card_id, current_user.id, db)
    
    # 如果指定了assignee_id，检查该用户是否是项目成员
    if assignment.assignee_id:
        assignee_member = db.query(ProjectMember).filter(
            ProjectMember.project_id == board.project_id,
            ProjectMember.user_id == assignment.assignee_id
        ).first()
        
        if not assignee_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee is not a member of this project"
            )
    
    card.assignee_id = assignment.assignee_id
    
    db.commit()
    db.refresh(card)
    
    return card

@router.delete("/{card_id}")
def delete_card(
    card_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除卡片"""
    card, list_obj, board = check_card_access(card_id, current_user.id, db)
    
    # 更新其他卡片的位置
    db.query(Card).filter(
        Card.list_id == card.list_id,
        Card.position > card.position
    ).update({Card.position: Card.position - 1})
    
    db.delete(card)
    db.commit()
    
    return {"message": "Card deleted successfully"}

@router.get("/user/assigned", response_model=List[CardSchema])
def read_user_assigned_cards(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取分配给当前用户的所有卡片"""
    cards = db.query(Card).filter(
        Card.assignee_id == current_user.id
    ).all()
    
    return cards

@router.get("/user/created", response_model=List[CardSchema])
def read_user_created_cards(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取当前用户创建的所有卡片"""
    cards = db.query(Card).filter(
        Card.creator_id == current_user.id
    ).all()
    
    return cards