import { defineStore } from 'pinia';
import { v4 as uuidv4 } from 'uuid';
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useToast } from 'vue-toastification';
import { apiService } from '../services/api';
import { useAuthStore } from './authStore';

// WebSocket连接管理
let socket = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_INTERVAL = 3000; // 3秒

export const useBoardStore = defineStore('board', () => {
  // 状态
  const boards = ref([]);
  const currentBoard = ref(null);
  const isLoading = ref(false);
  const isConnected = ref(false);
  const toast = useToast();
  const pendingChanges = ref([]);
  const authStore = useAuthStore();
  const recentBoardAccess = ref(new Map()); // 存储看板ID和最后访问时间的映射

  // 计算属性
  const getCurrentBoard = computed(() => currentBoard.value);
  const getBoardLists = computed(() => currentBoard.value?.lists || []);
  const getAllBoards = computed(() => boards.value);
  const connectionStatus = computed(() => isConnected.value ? '已连接' : '未连接');
  const getRecentBoards = computed(() => {
    // 获取最近访问的看板，按访问时间倒序排列，最多显示6个
    const recentEntries = Array.from(recentBoardAccess.value.entries())
      .sort((a, b) => b[1] - a[1]) // 按时间戳倒序
      .slice(0, 6); // 最多6个
    
    return recentEntries
      .map(([boardId]) => boards.value.find(board => board.id === boardId))
      .filter(board => board !== undefined); // 过滤掉已删除的看板
  });

  // 方法
  // 清除当前看板状态
  const clearCurrentBoard = () => {
    currentBoard.value = null;
    cleanup(); // 清理WebSocket连接
  };
  
  // 记录看板访问
  const recordBoardAccess = (boardId) => {
    if (boardId) {
      recentBoardAccess.value.set(boardId, Date.now());
      // 保存到localStorage以持久化
      try {
        const recentData = Object.fromEntries(recentBoardAccess.value);
        localStorage.setItem('recentBoardAccess', JSON.stringify(recentData));
      } catch (error) {
        console.warn('Failed to save recent board access to localStorage:', error);
      }
    }
  };
  
  // 从localStorage加载最近访问记录
  const loadRecentBoardAccess = () => {
    try {
      const saved = localStorage.getItem('recentBoardAccess');
      if (saved) {
        const recentData = JSON.parse(saved);
        recentBoardAccess.value = new Map(Object.entries(recentData).map(([k, v]) => [k, Number(v)]));
      }
    } catch (error) {
      console.warn('Failed to load recent board access from localStorage:', error);
    }
  };
  
  // 加载项目列表
  const loadProjects = async () => {
    if (!authStore.isAuthenticated) return;
    
    isLoading.value = true;
    try {
      const projects = await apiService.getProjects();
      boards.value = projects.map(project => ({
        id: project.id,
        name: project.name,
        description: project.description,
        lists: []
      }));
    } catch (error) {
      toast.error(`加载项目失败: ${error.message}`);
    } finally {
      isLoading.value = false;
    }
  };
  
  // 加载特定项目的完整数据
  const loadBoard = async (boardId) => {
    if (!authStore.isAuthenticated) return;
    
    isLoading.value = true;
    try {
      // 获取项目详情
      const project = await apiService.getProject(boardId);
      
      // 获取项目列表
      const lists = await apiService.getLists(boardId);
      
      // 获取每个列表的卡片
      const listsWithCards = await Promise.all(
        lists.map(async (list) => {
          const cards = await apiService.getCards(list.id);
          return {
            id: list.id,
            name: list.name,
            position: list.position,
            cards: cards.map(card => ({
              id: card.id,
              title: card.title,
              description: card.description || '',
              dueDate: card.due_date ? card.due_date.split('T')[0] : '',
              labels: card.labels ? card.labels.map(label => label.name) : [],
              assignedUsers: card.assignments ? card.assignments.map(assignment => ({
                id: assignment.user.id,
                name: assignment.user.full_name,
                email: assignment.user.email
              })) : []
            }))
          };
        })
      );
      
      const boardData = {
        id: project.id,
        name: project.name,
        description: project.description,
        lists: listsWithCards.sort((a, b) => a.position - b.position)
      };
      
      // 更新boards数组
      const boardIndex = boards.value.findIndex(b => b.id === boardId);
      if (boardIndex !== -1) {
        boards.value[boardIndex] = boardData;
      }
      // 注意：不再添加新的board，因为所有项目已在loadProjects中加载
      
      currentBoard.value = boardData;
      
      // 记录看板访问
      recordBoardAccess(boardId);
      
      // 只有在切换到不同看板时才重新建立连接
      if (!socket || !isConnected.value) {
        console.log('建立WebSocket连接');
        connectWebSocket(boardId);
      } else {
        console.log('WebSocket连接已存在，无需重新连接');
      }
      
    } catch (error) {
      toast.error(`加载看板失败: ${error.message}`);
    } finally {
      isLoading.value = false;
    }
  };

  // 创建新看板
  const createBoard = async (name, description = '') => {
    if (!authStore.isAuthenticated) return null;
    
    try {
      const newProject = await apiService.createProject({
        name,
        description
      });
      
      const newBoard = {
        id: newProject.id,
        name: newProject.name,
        description: newProject.description,
        lists: []
      };
      
      boards.value.push(newBoard);
      currentBoard.value = newBoard;
      
      toast.success('看板创建成功');
      return newBoard;
    } catch (error) {
      toast.error(`创建看板失败: ${error.message}`);
      return null;
    }
  };

  // 更新看板
  const updateBoard = async (boardId, updates) => {
    if (!authStore.isAuthenticated) return;
    
    try {
      await apiService.updateProject(boardId, updates);
      
      const boardIndex = boards.value.findIndex(b => b.id === boardId);
      if (boardIndex !== -1) {
        boards.value[boardIndex] = { ...boards.value[boardIndex], ...updates };
        if (currentBoard.value?.id === boardId) {
          currentBoard.value = boards.value[boardIndex];
        }
        toast.success('看板更新成功');
      }
    } catch (error) {
      toast.error(`更新看板失败: ${error.message}`);
    }
  };

  // 删除看板
  const deleteBoard = async (boardId) => {
    if (!authStore.isAuthenticated) return;
    
    try {
      await apiService.deleteProject(boardId);
      
      const boardIndex = boards.value.findIndex(b => b.id === boardId);
      if (boardIndex !== -1) {
        boards.value.splice(boardIndex, 1);
        if (currentBoard.value?.id === boardId) {
          currentBoard.value = boards.value.length > 0 ? boards.value[0] : null;
        }
        toast.success('看板删除成功');
      }
    } catch (error) {
      toast.error(`删除看板失败: ${error.message}`);
    }
  };

  // 添加列表
  const addList = async (name) => {
    if (!currentBoard.value || !authStore.isAuthenticated) return null;
    
    try {
      // 首先获取项目对应的看板
      const boards = await apiService.request(`/boards/project/${currentBoard.value.id}`);
      if (boards.length === 0) {
        throw new Error('项目没有关联的看板');
      }
      
      const boardId = boards[0].id; // 使用第一个看板
      const position = currentBoard.value.lists.length;
      
      const newList = await apiService.createList({
        name,
        position,
        board_id: boardId
      });
      
      const listData = {
        id: newList.id,
        name: newList.name,
        position: newList.position,
        cards: []
      };
      
      currentBoard.value.lists.push(listData);
      toast.success('列表添加成功');
      return listData;
    } catch (error) {
      toast.error(`添加列表失败: ${error.message}`);
      return null;
    }
  };

  // 更新列表
  const updateList = async (listId, updates) => {
    if (!currentBoard.value || !authStore.isAuthenticated) return;
    
    try {
      await apiService.updateList(listId, updates);
      
      const listIndex = currentBoard.value.lists.findIndex(l => l.id === listId);
      if (listIndex !== -1) {
        currentBoard.value.lists[listIndex] = { 
          ...currentBoard.value.lists[listIndex], 
          ...updates 
        };
      }
    } catch (error) {
      toast.error(`更新列表失败: ${error.message}`);
    }
  };

  // 删除列表
  const deleteList = async (listId) => {
    if (!currentBoard.value || !authStore.isAuthenticated) return;
    
    try {
      await apiService.deleteList(listId);
      
      const listIndex = currentBoard.value.lists.findIndex(l => l.id === listId);
      if (listIndex !== -1) {
        currentBoard.value.lists.splice(listIndex, 1);
        toast.success('列表删除成功');
      }
    } catch (error) {
      toast.error(`删除列表失败: ${error.message}`);
    }
  };

  // 添加卡片
  const addCard = async (listId, cardData) => {
    if (!currentBoard.value || !authStore.isAuthenticated) return null;
    
    try {
      const position = currentBoard.value.lists.find(l => l.id === listId)?.cards.length || 0;
      const newCard = await apiService.createCard({
        title: cardData.title,
        description: cardData.description || '',
        due_date: cardData.dueDate ? new Date(cardData.dueDate).toISOString() : null,
        position,
        list_id: listId,
        assigned_user_id: cardData.assignedUsers?.[0]?.id
      });
      
      const formattedCard = {
        id: newCard.id,
        title: newCard.title,
        description: newCard.description || '',
        dueDate: newCard.due_date ? newCard.due_date.split('T')[0] : '',
        labels: newCard.labels ? newCard.labels.map(label => label.name) : [],
        assignedUsers: newCard.assignments ? newCard.assignments.map(assignment => ({
          id: assignment.user.id,
          name: assignment.user.full_name,
          email: assignment.user.email
        })) : []
      };
      
      const list = currentBoard.value.lists.find(l => l.id === listId);
      if (list) {
        list.cards.push(formattedCard);
        toast.success('卡片添加成功');
        return formattedCard;
      }
    } catch (error) {
      toast.error(`添加卡片失败: ${error.message}`);
      return null;
    }
  };

  // 更新卡片
  const updateCard = async (listId, cardId, updates) => {
    if (!currentBoard.value || !authStore.isAuthenticated) return;
    
    try {
      const apiUpdates = {};
      if (updates.title) apiUpdates.title = updates.title;
      if (updates.description !== undefined) apiUpdates.description = updates.description;
      if (updates.dueDate) apiUpdates.due_date = new Date(updates.dueDate).toISOString();
      
      await apiService.updateCard(cardId, apiUpdates);
      
      const list = currentBoard.value.lists.find(l => l.id === listId);
      if (list) {
        const cardIndex = list.cards.findIndex(c => c.id === cardId);
        if (cardIndex !== -1) {
          list.cards[cardIndex] = { ...list.cards[cardIndex], ...updates };
        }
      }
    } catch (error) {
      toast.error(`更新卡片失败: ${error.message}`);
    }
  };

  // 删除卡片
  const deleteCard = async (listId, cardId) => {
    if (!currentBoard.value || !authStore.isAuthenticated) return;
    
    try {
      await apiService.deleteCard(cardId);
      
      const list = currentBoard.value.lists.find(l => l.id === listId);
      if (list) {
        const cardIndex = list.cards.findIndex(c => c.id === cardId);
        if (cardIndex !== -1) {
          list.cards.splice(cardIndex, 1);
          toast.success('卡片删除成功');
        }
      }
    } catch (error) {
      toast.error(`删除卡片失败: ${error.message}`);
    }
  };

  // 移动卡片
  const moveCard = async (sourceListId, targetListId, cardId, newIndex) => {
    if (!currentBoard.value || !authStore.isAuthenticated) return;
    
    console.log('BoardStore moveCard called:', {
      sourceListId,
      targetListId,
      cardId,
      newIndex
    });
    
    try {
      const moveData = {
        list_id: targetListId,
        position: newIndex
      };
      
      console.log('Calling API moveCard with:', cardId, moveData);
      
      await apiService.moveCard(cardId, moveData);
      
      console.log('API call successful, updating local state');
      
      const sourceList = currentBoard.value.lists.find(l => l.id === sourceListId);
      if (!sourceList) {
        console.warn('Source list not found:', sourceListId);
        return;
      }
      
      const cardIndex = sourceList.cards.findIndex(c => c.id === cardId);
      if (cardIndex === -1) {
        console.warn('Card not found in source list:', cardId);
        return;
      }
      
      const card = sourceList.cards[cardIndex];
      
      // 如果是同一列表内移动
      if (sourceListId === targetListId) {
        console.log('Moving card within same list');
        // 移除卡片
        sourceList.cards.splice(cardIndex, 1);
        // 在新位置插入卡片
        sourceList.cards.splice(newIndex, 0, card);
      } else {
        console.log('Moving card between different lists');
        // 跨列表移动
        // 从源列表移除
        sourceList.cards.splice(cardIndex, 1);
        // 找到目标列表
        const targetList = currentBoard.value.lists.find(l => l.id === targetListId);
        if (targetList) {
          // 添加到目标列表指定位置
          targetList.cards.splice(newIndex, 0, card);
        } else {
          console.warn('Target list not found:', targetListId);
        }
      }
      
      console.log('Card move completed successfully');
    } catch (error) {
      console.error('Move card error:', error);
      toast.error(`移动卡片失败: ${error.message}`);
    }
  };

  // WebSocket连接
  const connectWebSocket = (boardId) => {
    // 如果已经连接到同一个看板，不需要重新连接
    if (socket && isConnected.value && socket.url && socket.url.includes(`/ws/${boardId}`)) {
      console.log(`已连接到看板 ${boardId}，无需重新连接`);
      return;
    }

    // 先清理现有连接
    if (socket) {
      console.log('关闭现有WebSocket连接');
      socket.onclose = null; // 防止触发重连
      socket.onerror = null;
      socket.close();
      socket = null;
    }

    // 重置连接状态
    isConnected.value = false;
    reconnectAttempts = 0;

    try {
      const token = authStore.token;
      if (!token) {
        console.warn('没有认证token，无法连接WebSocket');
        return;
      }

      console.log(`正在连接WebSocket: boardId=${boardId}`);
      const wsUrl = `ws://localhost:8000/api/ws/${boardId}?token=${token}`;
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log(`WebSocket连接成功: ${wsUrl}`);
        isConnected.value = true;
        reconnectAttempts = 0;

        // 发送离线期间的待处理更改
        if (pendingChanges.value.length > 0) {
          console.log('发送待处理的更改:', pendingChanges.value);
          pendingChanges.value = [];
        }
      };

      socket.onmessage = (event) => {
        handleWebSocketMessage(event);
      };

      socket.onclose = (event) => {
        console.log('WebSocket连接关闭', event.code, event.reason);
        isConnected.value = false;
        // 只有在非主动关闭时才尝试重连
        if (event.code !== 1000 && currentBoard.value) {
          handleConnectionError();
        }
      };

      socket.onerror = (error) => {
        console.error('WebSocket错误:', error);
        isConnected.value = false;
      };

    } catch (error) {
      console.error('WebSocket连接错误:', error);
      handleConnectionError();
    }
  };

  // 处理连接错误
  const handleConnectionError = () => {
    isConnected.value = false;
    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
      reconnectAttempts++; 
      console.log(`重新连接尝试 ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}...`);
      setTimeout(() => {
        if (currentBoard.value) {
          connectWebSocket(currentBoard.value.id);
        }
      }, RECONNECT_INTERVAL);
    } else {
      toast.error('多次尝试后无法连接到服务器');
    }
  };

  // 广播变更
  const broadcastChange = (type, payload) => {
    if (isConnected.value && socket) {
      try {
        const message = JSON.stringify({
          type,
          payload,
          timestamp: new Date().toISOString()
        });
        socket.send(message);
        console.log('广播变更:', type, payload);
      } catch (error) {
        console.error('发送WebSocket消息失败:', error);
        // 存储离线期间的变更
        pendingChanges.value.push({ type, payload });
        toast.info('您正在离线工作。连接恢复后将同步更改。');
      }
    } else {
      // 存储离线期间的变更
      pendingChanges.value.push({ type, payload });
      toast.info('您正在离线工作。连接恢复后将同步更改。');
    }
  };

  // 处理收到的WebSocket消息
  const handleWebSocketMessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      console.log('收到WebSocket消息:', data);

      switch (data.type) {
        case 'board-updated':
        case 'board_updated':
          updateBoardFromServer(data.data || data.payload);
          break;
        case 'list-added':
        case 'list_created':
          addListFromServer(data.data || data.payload);
          break;
        case 'list-updated':
        case 'list_updated':
          updateListFromServer(data.data || data.payload);
          break;
        case 'list-deleted':
        case 'list_deleted':
          deleteListFromServer(data.data || data.payload);
          break;
        case 'card-added':
        case 'card_created':
          addCardFromServer(data.data || data.payload);
          break;
        case 'card-updated':
        case 'card_updated':
          updateCardFromServer(data.data || data.payload);
          break;
        case 'card-deleted':
        case 'card_deleted':
          deleteCardFromServer(data.data || data.payload);
          break;
        case 'card-moved':
        case 'card_moved':
          moveCardFromServer(data.data || data.payload);
          break;
        default:
          console.warn('未知的消息类型:', data.type);
      }
    } catch (error) {
      console.error('处理WebSocket消息时出错:', error);
    }
  };

  // 从服务器更新看板
  const updateBoardFromServer = (payload) => {
    if (!payload || !payload.id) return;
    
    const boardIndex = boards.value.findIndex(b => b.id === payload.id);
    if (boardIndex !== -1) {
      boards.value[boardIndex] = { ...boards.value[boardIndex], ...payload };
      if (currentBoard.value?.id === payload.id) {
        currentBoard.value = boards.value[boardIndex];
      }
    }
  };

  // 从服务器添加列表
  const addListFromServer = (payload) => {
    if (!payload) return;
    
    // 处理直接的列表数据格式
    if (payload.id && payload.name && currentBoard.value) {
      // 检查列表是否已存在
      if (!currentBoard.value.lists.some(l => l.id === payload.id)) {
        currentBoard.value.lists.push(payload);
        console.log('从WebSocket添加列表:', payload);
      }
      return;
    }
    
    // 处理包含boardId的格式（向后兼容）
    if (payload.boardId && payload.list && currentBoard.value?.id === payload.boardId) {
      if (!currentBoard.value.lists.some(l => l.id === payload.list.id)) {
        currentBoard.value.lists.push(payload.list);
      }
    }
  };

  // 从服务器更新列表
  const updateListFromServer = (payload) => {
    if (!payload || !payload.boardId || !payload.list) return;
    
    if (currentBoard.value?.id === payload.boardId) {
      const listIndex = currentBoard.value.lists.findIndex(l => l.id === payload.list.id);
      if (listIndex !== -1) {
        currentBoard.value.lists[listIndex] = { 
          ...currentBoard.value.lists[listIndex], 
          ...payload.list 
        };
      }
    }
  };

  // 从服务器删除列表
  const deleteListFromServer = (payload) => {
    if (!payload || !payload.boardId || !payload.listId) return;
    
    if (currentBoard.value?.id === payload.boardId) {
      const listIndex = currentBoard.value.lists.findIndex(l => l.id === payload.listId);
      if (listIndex !== -1) {
        currentBoard.value.lists.splice(listIndex, 1);
      }
    }
  };

  // 从服务器添加卡片
  const addCardFromServer = (payload) => {
    if (!payload) return;
    
    // 处理直接的卡片数据格式
    if (payload.id && payload.title && payload.list_id && currentBoard.value) {
      const list = currentBoard.value.lists.find(l => l.id === payload.list_id);
      if (list) {
        // 检查卡片是否已存在
        if (!list.cards.some(c => c.id === payload.id)) {
          // 转换数据格式以匹配前端期望的格式
          const cardData = {
            id: payload.id,
            title: payload.title,
            description: payload.description || '',
            dueDate: payload.due_date ? payload.due_date.split('T')[0] : '',
            labels: [],
            assignedUsers: []
          };
          list.cards.push(cardData);
          console.log('从WebSocket添加卡片:', cardData);
        }
      }
      return;
    }
    
    // 处理包含boardId的格式（向后兼容）
    if (payload.boardId && payload.listId && payload.card && currentBoard.value?.id === payload.boardId) {
      const list = currentBoard.value.lists.find(l => l.id === payload.listId);
      if (list) {
        if (!list.cards.some(c => c.id === payload.card.id)) {
          list.cards.push(payload.card);
        }
      }
    }
  };

  // 从服务器更新卡片
  const updateCardFromServer = (payload) => {
    if (!payload || !payload.boardId || !payload.listId || !payload.card) return;
    
    if (currentBoard.value?.id === payload.boardId) {
      const list = currentBoard.value.lists.find(l => l.id === payload.listId);
      if (list) {
        const cardIndex = list.cards.findIndex(c => c.id === payload.card.id);
        if (cardIndex !== -1) {
          list.cards[cardIndex] = { ...list.cards[cardIndex], ...payload.card };
        }
      }
    }
  };

  // 从服务器删除卡片
  const deleteCardFromServer = (payload) => {
    if (!payload || !payload.boardId || !payload.listId || !payload.cardId) return;
    
    if (currentBoard.value?.id === payload.boardId) {
      const list = currentBoard.value.lists.find(l => l.id === payload.listId);
      if (list) {
        const cardIndex = list.cards.findIndex(c => c.id === payload.cardId);
        if (cardIndex !== -1) {
          list.cards.splice(cardIndex, 1);
        }
      }
    }
  };

  // 从服务器移动卡片
  const moveCardFromServer = (payload) => {
    if (!payload || !payload.boardId || !payload.sourceListId || 
        !payload.targetListId || !payload.cardId || payload.newIndex === undefined) {
      return;
    }
    
    if (currentBoard.value?.id === payload.boardId) {
      const sourceList = currentBoard.value.lists.find(l => l.id === payload.sourceListId);
      if (!sourceList) return;
      
      const cardIndex = sourceList.cards.findIndex(c => c.id === payload.cardId);
      if (cardIndex === -1) return;
      
      const card = sourceList.cards[cardIndex];
      
      // 如果是同一列表内移动
      if (payload.sourceListId === payload.targetListId) {
        // 移除卡片
        sourceList.cards.splice(cardIndex, 1);
        // 在新位置插入卡片
        sourceList.cards.splice(payload.newIndex, 0, card);
      } else {
        // 跨列表移动
        // 从源列表移除
        sourceList.cards.splice(cardIndex, 1);
        // 找到目标列表
        const targetList = currentBoard.value.lists.find(l => l.id === payload.targetListId);
        if (targetList) {
          // 添加到目标列表指定位置
          targetList.cards.splice(payload.newIndex, 0, card);
        }
      }
    }
  };

  // 初始化
  const initialize = async () => {
    // 加载最近访问记录
    loadRecentBoardAccess();
    
    // 如果已认证，加载项目列表
    if (authStore.isAuthenticated) {
      await loadProjects();
    }
  };

  // 清理函数
  const cleanup = () => {
    console.log('清理WebSocket连接');
    if (socket) {
      // 防止触发重连
      socket.onclose = null;
      socket.onerror = null;
      socket.close();
      socket = null;
    }
    isConnected.value = false;
    reconnectAttempts = 0;
  };

  // 初始化
  initialize();

  return {
    // 状态
    boards,
    currentBoard,
    isLoading,
    isConnected,
    
    // 计算属性
    getCurrentBoard,
    getBoardLists,
    getAllBoards,
    getRecentBoards,
    connectionStatus,
    
    // 方法
    initialize,
    clearCurrentBoard,
    loadBoard,
    createBoard,
    updateBoard,
    deleteBoard,
    addList,
    updateList,
    deleteList,
    addCard,
    updateCard,
    deleteCard,
    moveCard,
    
    // WebSocket
    connectWebSocket,
    cleanup
  };
});