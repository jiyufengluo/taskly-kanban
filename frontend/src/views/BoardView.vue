<template>
  <div class="board-view">
    <!-- Board Header Section -->
    <div class="board-header bg-white border-b shadow-sm">
      <div class="container mx-auto px-4 py-3">
        <div class="flex items-center justify-between">
          <!-- Board Title and Editing -->
          <div class="flex items-center">
            <div v-if="!isEditingTitle" @click="startEditingBoardTitle" class="flex items-center cursor-pointer">
              <h1 class="text-xl font-semibold text-gray-800">{{ currentBoard?.name || '正在加载看板...' }}</h1>
              <i class="fas fa-pencil-alt ml-2 text-gray-500 hover:text-blue-500 text-sm"></i>
            </div>
            <div v-else class="flex items-center">
              <input 
                ref="boardTitleInput"
                v-model="editableBoardTitle"
                @blur="saveBoardTitle"
                @keyup.enter="saveBoardTitle"
                @keyup.esc="cancelEditingBoardTitle"
                class="text-xl font-semibold px-2 py-1 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                type="text"
              />
            </div>
            
            <div class="ml-4 flex items-center text-sm">
              <span :class="connectionClass" class="flex items-center">
                <i class="fas fa-circle mr-1 text-xs"></i>
                {{ connectionStatus }}
              </span>
            </div>
          </div>
          
          <!-- Board Actions -->
          <div class="flex items-center space-x-3">
            <!-- View Dashboard Button -->
            <router-link 
              to="/dashboard" 
              class="flex items-center px-3 py-2 bg-blue-50 text-blue-600 rounded-md hover:bg-blue-100 transition-colors"
            >
              <i class="fas fa-chart-line mr-2"></i>
              <span class="text-sm font-medium">仪表板</span>
            </router-link>
            
            <!-- More Actions Dropdown -->
            <div class="relative" ref="actionsDropdown">
              <button 
                @click="toggleActionsDropdown" 
                class="px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
              >
                <i class="fas fa-ellipsis-h"></i>
              </button>
              
              <div 
                v-if="showActionsDropdown" 
                class="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 py-1"
              >
                <button 
                  @click="exportBoard" 
                  class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  <i class="fas fa-file-export mr-2"></i> 导出看板
                </button>
                <button 
                  @click="showDeleteBoardModal = true" 
                  class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
                >
                  <i class="fas fa-trash mr-2"></i> 删除看板
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Board Content -->
    <div class="board-content bg-blue-50 flex-grow p-4 overflow-auto">
      <div v-if="isLoading" class="flex justify-center items-center h-full">
        <div class="text-center">
          <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
          <p class="mt-3 text-gray-600">正在加载看板...</p>
        </div>
      </div>
      
      <div v-else-if="!currentBoard" class="flex justify-center items-center h-full">
        <div class="text-center">
          <i class="fas fa-clipboard-list text-gray-400 text-5xl"></i>
          <p class="mt-3 text-gray-600">未选择看板。请选择或创建一个看板。</p>
          <button 
            @click="showCreateBoardModal = true" 
            class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            <i class="fas fa-plus mr-2"></i> 创建新看板
          </button>
        </div>
      </div>
      
      <div v-else class="h-full">
        <!-- Kanban Lists Container -->
        <div class="kanban-container flex space-x-4 h-full items-start">
          <draggable 
            :list="boardLists" 
            :group="{ name: 'lists' }"
            item-key="id"
            class="flex space-x-4 h-full items-start"
            :animation="200"
            handle=".kanban-list"
          >
            <template #item="{ element }">
              <KanbanList :list="element" />
            </template>
          </draggable>
          
          <!-- Add List Button -->
          <div class="min-w-[300px] h-fit">
            <div v-if="!isAddingList" class="bg-gray-100 bg-opacity-80 rounded-lg p-3 shadow-sm hover:bg-gray-200 transition-colors cursor-pointer" @click="startAddingList">
              <div class="flex items-center justify-center py-2">
                <i class="fas fa-plus mr-2"></i>
                <span>添加另一个列表</span>
              </div>
            </div>
            
            <div v-else class="bg-gray-100 rounded-lg p-3 shadow-sm">
              <input 
                ref="newListInput"
                v-model="newListName"
                placeholder="请输入列表标题..."
                class="w-full p-2 text-sm border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 mb-2"
                @keyup.enter="addNewList"
              />
              <div class="flex gap-2">
                <button 
                  @click="addNewList" 
                  class="px-3 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 transition-colors"
                >
                  添加列表
                </button>
                <button 
                  @click="cancelAddingList" 
                  class="px-3 py-2 text-gray-500 text-sm hover:text-gray-700 transition-colors"
                >
                  取消
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Create Board Modal -->
    <div v-if="showCreateBoardModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="showCreateBoardModal = false">
      <div class="bg-white rounded-lg p-6 w-96 max-w-full">
        <h3 class="text-lg font-medium mb-4">创建新看板</h3>
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">看板名称</label>
          <input 
            v-model="newBoardName" 
            class="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="请输入看板名称"
            @keyup.enter="createNewBoard"
          />
        </div>
        <div class="flex justify-end gap-2">
          <button 
            @click="showCreateBoardModal = false" 
            class="px-4 py-2 bg-gray-100 rounded-md hover:bg-gray-200"
          >
            取消
          </button>
          <button 
            @click="createNewBoard" 
            class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            :disabled="!newBoardName.trim()"
          >
            创建
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Board Confirmation Modal -->
    <div v-if="showDeleteBoardModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="showDeleteBoardModal = false">
      <div class="bg-white rounded-lg p-6 w-96 max-w-full">
        <h3 class="text-lg font-medium mb-4">删除看板？</h3>
        <p class="text-gray-600 mb-4">
          您确定要删除 "{{ currentBoard?.name }}" 吗？此操作无法撤销。
        </p>
        <div class="flex justify-end gap-2">
          <button 
            @click="showDeleteBoardModal = false" 
            class="px-4 py-2 bg-gray-100 rounded-md hover:bg-gray-200"
          >
            Cancel
          </button>
          <button 
            @click="deleteCurrentBoard" 
            class="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600"
          >
            删除
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onBeforeUnmount, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import draggable from 'vuedraggable';
import { useBoardStore } from '../stores/boardStore';
import KanbanList from '../components/KanbanList.vue';

// Store and router
const boardStore = useBoardStore();
const router = useRouter();
const route = useRoute();

// Reactive state
const isEditingTitle = ref(false);
const editableBoardTitle = ref('');
const boardTitleInput = ref(null);
const showActionsDropdown = ref(false);
const actionsDropdown = ref(null);
const isAddingList = ref(false);
const newListName = ref('');
const newListInput = ref(null);
const showCreateBoardModal = ref(false);
const newBoardName = ref('');
const showDeleteBoardModal = ref(false);

// Computed properties
const isLoading = computed(() => boardStore.isLoading);
const currentBoard = computed(() => boardStore.getCurrentBoard);
const boardLists = computed(() => boardStore.getBoardLists);
const connectionStatus = computed(() => boardStore.connectionStatus);
const connectionClass = computed(() => {
  return boardStore.isConnected
    ? 'text-green-600'
    : 'text-red-600';
});

// Methods for board actions
const startEditingBoardTitle = () => {
  if (!currentBoard.value) return;
  
  editableBoardTitle.value = currentBoard.value.name;
  isEditingTitle.value = true;
  nextTick(() => {
    boardTitleInput.value.focus();
  });
};

const saveBoardTitle = () => {
  if (!currentBoard.value) return;
  
  if (editableBoardTitle.value.trim()) {
    boardStore.updateBoard(currentBoard.value.id, { name: editableBoardTitle.value.trim() });
  }
  isEditingTitle.value = false;
};

const cancelEditingBoardTitle = () => {
  isEditingTitle.value = false;
};

const toggleActionsDropdown = () => {
  showActionsDropdown.value = !showActionsDropdown.value;
};

const exportBoard = () => {
  if (!currentBoard.value) return;
  
  // Create a JSON export of the current board
  const boardData = JSON.stringify(currentBoard.value, null, 2);
  const blob = new Blob([boardData], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${currentBoard.value.name.replace(/\s+/g, '_')}_export.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  
  showActionsDropdown.value = false;
};

const deleteCurrentBoard = () => {
  if (!currentBoard.value) return;
  
  const boardId = currentBoard.value.id;
  boardStore.deleteBoard(boardId);
  showDeleteBoardModal.value = false;
  router.push('/');
};

// Methods for list management
const startAddingList = () => {
  isAddingList.value = true;
  newListName.value = '';
  nextTick(() => {
    newListInput.value.focus();
  });
};

const addNewList = () => {
  if (newListName.value.trim()) {
    boardStore.addList(newListName.value.trim());
    newListName.value = '';
    // Keep form open for adding multiple lists
    nextTick(() => {
      newListInput.value.focus();
    });
  }
};

const cancelAddingList = () => {
  isAddingList.value = false;
  newListName.value = '';
};

// Methods for board management
const createNewBoard = () => {
  if (newBoardName.value.trim()) {
    const newBoard = boardStore.createBoard(newBoardName.value.trim());
    newBoardName.value = '';
    showCreateBoardModal.value = false;
    
    // Navigate to the new board
    if (newBoard) {
      router.push(`/board/${newBoard.id}`);
    }
  }
};

// Click outside handler for dropdown
const handleClickOutside = (event) => {
  if (actionsDropdown.value && !actionsDropdown.value.contains(event.target)) {
    showActionsDropdown.value = false;
  }
};

// Lifecycle hooks
onMounted(() => {
  document.addEventListener('click', handleClickOutside);
  
  // Load board from route params if available
  const boardId = route.params.id;
  if (boardId) {
    boardStore.loadBoard(boardId);
  }
});

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside);
  boardStore.cleanup(); // Clean up WebSocket connection
});

// Watch for route changes to load different boards
watch(
  () => route.params.id,
  (newBoardId) => {
    if (newBoardId) {
      boardStore.loadBoard(newBoardId);
    }
  }
);
</script>

<style scoped>
.board-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.board-content {
  flex: 1;
  overflow-x: auto;
}

.kanban-container {
  min-height: 100%;
  padding-bottom: 20px;
}
</style>