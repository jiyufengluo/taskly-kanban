<template>
  <div class="home-view h-screen flex flex-col">
    <!-- Hero Section -->
    <div class="hero-section bg-gradient-to-r from-blue-500 to-indigo-600 text-white py-16">
      <div class="container mx-auto px-4">
        <div class="max-w-3xl mx-auto text-center">
          <h1 class="text-4xl md:text-5xl font-bold mb-6 animate__animated animate__fadeInDown">
欢迎使用 Taskly
          </h1>
          <p class="text-xl mb-8 animate__animated animate__fadeInUp animate__delay-1s">
简单而强大的项目管理平台，帮助团队高效协作完成工作。
          </p>
          <div class="flex justify-center gap-4 animate__animated animate__fadeInUp animate__delay-2s">
            <button 
              @click="goToFirstBoard" 
              class="px-6 py-3 bg-white text-blue-600 font-semibold rounded-md hover:bg-blue-50 transition-colors"
            >
              <i class="fas fa-play mr-2"></i> 开始使用
            </button>
            <router-link 
              to="/dashboard" 
              class="px-6 py-3 border border-white text-white font-semibold rounded-md hover:bg-white hover:bg-opacity-10 transition-colors"
            >
              <i class="fas fa-chart-line mr-2"></i> 仪表板
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- Features Section -->
    <div class="features-section py-16 bg-gray-50 flex-grow">
      <div class="container mx-auto px-4">
        <h2 class="text-3xl font-bold text-center mb-12 text-gray-800">为什么选择 Taskly？</h2>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <!-- Feature 1 -->
          <div class="feature-card bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow">
            <div class="text-blue-500 mb-4 text-3xl">
              <i class="fas fa-tasks"></i>
            </div>
            <h3 class="text-xl font-semibold mb-3 text-gray-800">直观的看板</h3>
            <p class="text-gray-600">
              通过拖拽操作轻松组织任务。创建符合团队流程的自定义工作流。
            </p>
          </div>
          
          <!-- Feature 2 -->
          <div class="feature-card bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow">
            <div class="text-blue-500 mb-4 text-3xl">
              <i class="fas fa-users"></i>
            </div>
            <h3 class="text-xl font-semibold mb-3 text-gray-800">团队协作</h3>
            <p class="text-gray-600">
              通过实时更新无缝协作。分配任务、分享反馈，团队共同跟踪进度。
            </p>
          </div>
          
          <!-- Feature 3 -->
          <div class="feature-card bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow">
            <div class="text-blue-500 mb-4 text-3xl">
              <i class="fas fa-robot"></i>
            </div>
            <h3 class="text-xl font-semibold mb-3 text-gray-800">AI 助手</h3>
            <p class="text-gray-600">
              让我们的AI助手帮助您进行数据分析、报告生成和工作流优化。
            </p>
          </div>
        </div>
        
        <!-- Recent Boards Section -->
        <div class="mt-16">
          <!-- <h2 class="text-2xl font-bold text-gray-800 mb-6">您的最近看板</h2> -->
          
          <div v-if="recentBoards.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div 
              v-for="board in recentBoards" 
              :key="board.id" 
              class="board-card bg-white p-5 rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer"
              @click="navigateToBoard(board.id)"
            >
              <h3 class="text-lg font-semibold mb-2 text-gray-800">{{ board.name }}</h3>
              <div class="flex justify-between items-center">
                <span class="text-sm text-gray-500">
                  {{ board.lists.length }} 个列表 · {{ getTotalCards(board) }} 张卡片
                </span>
                <span class="w-2 h-2 rounded-full" :class="getRandomColorClass()"></span>
              </div>
            </div>
          </div>
          
          <div v-else class="text-center py-8 bg-white rounded-lg shadow-sm">
            <div class="text-5xl text-gray-300 mb-3">
              <i class="fas fa-clipboard-list"></i>
            </div>
            <p class="text-gray-600 mb-4">还没有看板。创建您的第一个看板开始使用吧。</p>
            <button 
              @click="showCreateBoardModal = true" 
              class="px-5 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 transition-colors"
            >
              <i class="fas fa-plus mr-2"></i> 创建看板
            </button>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useBoardStore } from '../stores/boardStore';

// Router and store
const router = useRouter();
const boardStore = useBoardStore();

// State
const showCreateBoardModal = ref(false);
const newBoardName = ref('');

// Computed
const recentBoards = computed(() => {
  return boardStore.getRecentBoards;
});

// Methods
const navigateToBoard = (boardId) => {
  router.push(`/board/${boardId}`);
};

const goToFirstBoard = () => {
  if (recentBoards.value.length > 0) {
    navigateToBoard(recentBoards.value[0].id);
  } else {
    showCreateBoardModal.value = true;
  }
};

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

const getTotalCards = (board) => {
  let total = 0;
  board.lists.forEach(list => {
    total += list.cards.length;
  });
  return total;
};

const getRandomColorClass = () => {
  const colors = [
    'bg-blue-500',
    'bg-green-500',
    'bg-yellow-500',
    'bg-purple-500',
    'bg-red-500',
    'bg-indigo-500',
    'bg-pink-500'
  ];
  
  return colors[Math.floor(Math.random() * colors.length)];
};
</script>

<style scoped>
.home-view {
  background-color: #f9fafb;
}

.feature-card, .board-card {
  transition: transform 0.2s;
}

.feature-card:hover, .board-card:hover {
  transform: translateY(-5px);
}
</style>