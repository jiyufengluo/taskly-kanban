from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models import User, Project, Board, List as BoardList, ProjectMember
from app.schemas import (
    Board as BoardSchema,
    BoardCreate,
    BoardUpdate,
    BoardWithLists,
    List as ListSchema,
    ListCreate,
    ListUpdate,
    ListPositionUpdate
)
from app.api.websocket import WebSocketNotifier
import asyncio

router = APIRouter()

def check_project_access(project_id: int, user_id: int, db: Session):
    """检查用户是否有项目访问权限"""
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this project"
        )
    return member

def check_project_write_access(project_id: int, user_id: int, db: Session):
    """检查用户是否有项目写入权限"""
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this project"
        )
    return member

# 看板管理
@router.post("/", response_model=BoardSchema, status_code=status.HTTP_201_CREATED)
def create_board(
    board: BoardCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建新看板"""
    # 检查项目访问权限
    check_project_write_access(board.project_id, current_user.id, db)
    
    # 检查项目是否存在
    project = db.query(Project).filter(Project.id == board.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    db_board = Board(
        name=board.name,
        description=board.description,
        project_id=board.project_id
    )
    
    db.add(db_board)
    db.commit()
    db.refresh(db_board)
    
    return db_board

@router.get("/project/{project_id}", response_model=List[BoardSchema])
def read_project_boards(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取项目的所有看板"""
    # 检查项目访问权限
    check_project_access(project_id, current_user.id, db)
    
    boards = db.query(Board).filter(Board.project_id == project_id).all()
    return boards

@router.get("/{board_id}", response_model=BoardWithLists)
def read_board(
    board_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取看板详情（包含列表）"""
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    
    # 检查项目访问权限
    check_project_access(board.project_id, current_user.id, db)
    
    return board

@router.put("/{board_id}", response_model=BoardSchema)
def update_board(
    board_id: int,
    board_update: BoardUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新看板信息"""
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    
    # 检查项目写入权限
    check_project_write_access(board.project_id, current_user.id, db)
    
    # 更新看板信息
    update_data = board_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(board, field, value)
    
    db.commit()
    db.refresh(board)
    
    return board

@router.delete("/{board_id}")
def delete_board(
    board_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除看板"""
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    
    # 检查项目写入权限
    check_project_write_access(board.project_id, current_user.id, db)
    
    db.delete(board)
    db.commit()
    
    return {"message": "Board deleted successfully"}

# 列表管理
@router.post("/lists", response_model=ListSchema, status_code=status.HTTP_201_CREATED)
def create_list(
    list_data: ListCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建新列表"""
    # 检查看板是否存在
    board = db.query(Board).filter(Board.id == list_data.board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    
    # 检查项目写入权限
    check_project_write_access(board.project_id, current_user.id, db)
    
    # 如果没有指定位置，设置为最后一个位置
    if list_data.position == 0:
        max_position = db.query(BoardList).filter(
            BoardList.board_id == list_data.board_id
        ).count()
        list_data.position = max_position
    
    db_list = BoardList(
        name=list_data.name,
        position=list_data.position,
        board_id=list_data.board_id
    )
    
    db.add(db_list)
    db.commit()
    db.refresh(db_list)
    
    # 触发WebSocket通知
    try:
        from app.api.websocket import notifier
        list_data_ws = {
            "id": db_list.id,
            "name": db_list.name,
            "position": db_list.position,
            "cards": []
        }
        asyncio.create_task(notifier.notify_list_created(board.project_id, list_data_ws, current_user.id))
        print(f"WebSocket notification sent for list creation: {db_list.id}")
    except Exception as e:
        print(f"Failed to send WebSocket notification for list creation: {e}")
    
    return db_list

@router.get("/lists/{list_id}", response_model=ListSchema)
def read_list(
    list_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取列表详情"""
    list_obj = db.query(BoardList).filter(BoardList.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    # 检查项目访问权限
    board = db.query(Board).filter(Board.id == list_obj.board_id).first()
    check_project_access(board.project_id, current_user.id, db)
    
    return list_obj

@router.put("/lists/{list_id}", response_model=ListSchema)
def update_list(
    list_id: int,
    list_update: ListUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新列表信息"""
    list_obj = db.query(BoardList).filter(BoardList.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    # 检查项目写入权限
    board = db.query(Board).filter(Board.id == list_obj.board_id).first()
    check_project_write_access(board.project_id, current_user.id, db)
    
    # 更新列表信息
    update_data = list_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(list_obj, field, value)
    
    db.commit()
    db.refresh(list_obj)
    
    return list_obj

@router.put("/lists/{list_id}/position", response_model=ListSchema)
def update_list_position(
    list_id: int,
    position_update: ListPositionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新列表位置"""
    list_obj = db.query(BoardList).filter(BoardList.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    # 检查项目写入权限
    board = db.query(Board).filter(Board.id == list_obj.board_id).first()
    check_project_write_access(board.project_id, current_user.id, db)
    
    old_position = list_obj.position
    new_position = position_update.position
    
    # 更新其他列表的位置
    if new_position > old_position:
        # 向后移动，其他列表向前移动
        db.query(BoardList).filter(
            BoardList.board_id == list_obj.board_id,
            BoardList.position > old_position,
            BoardList.position <= new_position,
            BoardList.id != list_id
        ).update({BoardList.position: BoardList.position - 1})
    elif new_position < old_position:
        # 向前移动，其他列表向后移动
        db.query(BoardList).filter(
            BoardList.board_id == list_obj.board_id,
            BoardList.position >= new_position,
            BoardList.position < old_position,
            BoardList.id != list_id
        ).update({BoardList.position: BoardList.position + 1})
    
    # 更新当前列表位置
    list_obj.position = new_position
    
    db.commit()
    db.refresh(list_obj)
    
    return list_obj

@router.delete("/lists/{list_id}")
def delete_list(
    list_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除列表"""
    list_obj = db.query(BoardList).filter(BoardList.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    # 检查项目写入权限
    board = db.query(Board).filter(Board.id == list_obj.board_id).first()
    check_project_write_access(board.project_id, current_user.id, db)
    
    # 更新其他列表的位置
    db.query(BoardList).filter(
        BoardList.board_id == list_obj.board_id,
        BoardList.position > list_obj.position
    ).update({BoardList.position: BoardList.position - 1})
    
    db.delete(list_obj)
    db.commit()
    
    return {"message": "List deleted successfully"}