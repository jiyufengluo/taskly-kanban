from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_active_user, verify_board_access
from app.models.models import User, Board, List, Card
from app.models.schemas import BoardCreate, BoardResponse, BoardUpdate
from app.core.redis import cache
from app.services.activity_service import log_activity
from datetime import datetime
import json

router = APIRouter()


@router.get("/", response_model=List[BoardResponse])
async def get_boards(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户的看板列表"""
    # 尝试从缓存获取
    cache_key = f"boards:user:{current_user.id}:{skip}:{limit}"
    cached_boards = cache.get(cache_key)
    
    if cached_boards:
        return json.loads(cached_boards)
    
    # 从数据库获取用户有权限的看板
    boards = db.query(Board).filter(
        (Board.owner_id == current_user.id) | 
        (Board.members.contains(current_user))
    ).offset(skip).limit(limit).all()
    
    # 缓存结果
    boards_data = []
    for board in boards:
        board_dict = {
            "id": board.id,
            "name": board.name,
            "description": board.description,
            "is_active": board.is_active,
            "owner_id": board.owner_id,
            "created_at": board.created_at.isoformat(),
            "updated_at": board.updated_at.isoformat(),
            "members": []
        }
        boards_data.append(board_dict)
    
    cache.set(cache_key, json.dumps(boards_data), ttl=300)  # 5分钟缓存
    
    return boards


@router.post("/", response_model=BoardResponse)
async def create_board(
    board_data: BoardCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建新看板"""
    # 创建看板
    new_board = Board(
        name=board_data.name,
        description=board_data.description,
        is_active=board_data.is_active,
        owner_id=current_user.id
    )
    
    db.add(new_board)
    db.commit()
    db.refresh(new_board)
    
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
            board_id=new_board.id
        )
        db.add(new_list)
    
    db.commit()
    
    # 记录活动
    log_activity(
        db=db,
        user_id=current_user.id,
        action_type="create",
        entity_type="board",
        entity_id=new_board.id,
        changes={"name": new_board.name, "description": new_board.description}
    )
    
    # 清除缓存
    cache.clear_pattern(f"boards:user:{current_user.id}:*")
    
    return new_board


@router.get("/{board_id}", response_model=BoardResponse)
async def get_board(
    board_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取看板详情"""
    # 验证访问权限
    verify_board_access(board_id, current_user, db)
    
    # 尝试从缓存获取
    cache_key = f"board:{board_id}"
    cached_board = cache.get(cache_key)
    
    if cached_board:
        board_data = json.loads(cached_board)
        return BoardResponse(**board_data)
    
    # 从数据库获取
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    
    # 缓存结果
    board_data = {
        "id": board.id,
        "name": board.name,
        "description": board.description,
        "is_active": board.is_active,
        "owner_id": board.owner_id,
        "created_at": board.created_at.isoformat(),
        "updated_at": board.updated_at.isoformat(),
        "members": []
    }
    cache.set(cache_key, json.dumps(board_data), ttl=300)  # 5分钟缓存
    
    return board


@router.put("/{board_id}", response_model=BoardResponse)
async def update_board(
    board_id: int,
    board_update: BoardUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新看板"""
    # 验证访问权限
    verify_board_access(board_id, current_user, db)
    
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    
    # 只有看板所有者可以更新看板
    if board.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only board owner can update the board"
        )
    
    # 更新看板信息
    update_data = board_update.dict(exclude_unset=True)
    changes = {}
    for field, value in update_data.items():
        if getattr(board, field) != value:
            changes[field] = {"old": getattr(board, field), "new": value}
        setattr(board, field, value)
    
    if changes:
        db.commit()
        db.refresh(board)
        
        # 记录活动
        log_activity(
            db=db,
            user_id=current_user.id,
            action_type="update",
            entity_type="board",
            entity_id=board.id,
            changes=changes
        )
    
    # 清除缓存
    cache.delete(f"board:{board_id}")
    cache.clear_pattern(f"boards:user:{current_user.id}:*")
    
    return board


@router.delete("/{board_id}")
async def delete_board(
    board_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除看板"""
    # 验证访问权限
    verify_board_access(board_id, current_user, db)
    
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    
    # 只有看板所有者可以删除看板
    if board.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only board owner can delete the board"
        )
    
    board_name = board.name
    db.delete(board)
    db.commit()
    
    # 记录活动
    log_activity(
        db=db,
        user_id=current_user.id,
        action_type="delete",
        entity_type="board",
        entity_id=board_id,
        changes={"name": board_name}
    )
    
    # 清除缓存
    cache.delete(f"board:{board_id}")
    cache.clear_pattern(f"boards:user:{current_user.id}:*")
    
    return {"message": "Board deleted successfully"}