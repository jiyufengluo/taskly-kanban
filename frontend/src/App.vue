<template>
  <div class="app-container">
    <!-- Show login view when not authenticated -->
    <div v-if="!isAuthenticated" class="login-layout">
      <router-view></router-view>
    </div>
    
    <!-- Show main app when authenticated -->
    <div v-else class="app-layout">
      <!-- Side Navigation -->
      <aside class="sidebar bg-gray-800 text-white">
        <div class="sidebar-header p-4 border-b border-gray-700">
          <router-link to="/" class="logo flex items-center gap-2" @click="handleLogoClick">
            <div class="logo-icon bg-blue-500 text-white w-8 h-8 rounded-md flex items-center justify-center">
              <i class="fas fa-tasks"></i>
            </div>
            <h1 class="text-xl font-bold">Taskly</h1>
          </router-link>
        </div>
        
        <div class="sidebar-content p-4">
          <!-- Main Navigation -->
          <nav class="main-nav mb-6">
            <h2 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
              导航
            </h2>
            <ul class="space-y-1">
              <li>
                <router-link 
                  to="/" 
                  class="flex items-center px-3 py-2 rounded-md transition-colors"
                  :class="[
                    $route.path === '/' 
                      ? 'bg-blue-600 text-white' 
                      : 'hover:bg-gray-700 text-gray-300'
                  ]"
                  @click="handleLogoClick"
                >
                  <i class="fas fa-home mr-2 text-sm"></i>
                  <span class="text-sm">首页</span>
                </router-link>
              </li>
            </ul>
          </nav>
          
          <!-- Boards Navigation -->
          <nav class="boards-nav mb-6">
            <h2 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
              您的看板
            </h2>
            <ul class="space-y-1">
              <li v-for="board in boardStore.getAllBoards" :key="board.id">
                <router-link 
                  :to="`/board/${board.id}`" 
                  class="flex items-center px-3 py-2 rounded-md transition-colors"
                  :class="[
                    boardStore.currentBoard?.id === board.id 
                      ? 'bg-blue-600 text-white' 
                      : 'hover:bg-gray-700 text-gray-300'
                  ]"
                >
                  <i class="fas fa-clipboard-list mr-2 text-sm"></i>
                  <span class="text-sm truncate">{{ board.name }}</span>
                </router-link>
              </li>
              <li>
                <button 
                  @click="showCreateBoardModal = true" 
                  class="flex items-center w-full text-left px-3 py-2 rounded-md text-blue-400 hover:bg-gray-700 transition-colors"
                >
                  <i class="fas fa-plus mr-2 text-sm"></i>
                  <span class="text-sm">创建新看板</span>
                </button>
              </li>
            </ul>
          </nav>
          
          <!-- Quick Links -->
          <div class="quick-links">
            <h2 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
              快速链接
            </h2>
            <ul class="space-y-1">
              <li>
                <router-link to="/dashboard" class="flex items-center px-3 py-2 rounded-md text-gray-300 hover:bg-gray-700 transition-colors">
                  <i class="fas fa-chart-line mr-2 text-sm"></i>
                  <span class="text-sm">仪表板</span>
                </router-link>
              </li>
              <li>
                <router-link to="/settings" class="flex items-center px-3 py-2 rounded-md text-gray-300 hover:bg-gray-700 transition-colors">
                  <i class="fas fa-cog mr-2 text-sm"></i>
                  <span class="text-sm">设置</span>
                </router-link>
              </li>
            </ul>
          </div>
        </div>
        
        <div class="sidebar-footer mt-auto p-4 border-t border-gray-700">
          <div class="flex items-center">
            <div class="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center text-sm font-medium">
              {{ currentUser?.full_name?.charAt(0)?.toUpperCase() || 'U' }}
            </div>
            <div class="ml-2">
              <p class="text-sm font-medium">{{ currentUser?.full_name || 'User' }}</p>
              <p class="text-xs text-gray-400">{{ currentUser?.email || 'user@example.com' }}</p>
            </div>
            <button @click="handleLogout" class="ml-auto text-gray-400 hover:text-white">
              <i class="fas fa-sign-out-alt"></i>
            </button>
          </div>
        </div>
      </aside>

      <!-- Main Content -->
      <main class="main-content flex-grow bg-gray-50">
        <router-view></router-view>
      </main>
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
import { ref, computed, watch, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useBoardStore } from './stores/boardStore';
import { useAuthStore } from './stores/authStore';

// Router and store
const router = useRouter();
const route = useRoute();
const boardStore = useBoardStore();
const authStore = useAuthStore();

// 监听路由变化，当不在看板页面时清除currentBoard状态
watch(() => route.path, (newPath) => {
  // 如果不是看板页面，清除当前看板状态
  if (!newPath.startsWith('/board/')) {
    boardStore.clearCurrentBoard();
  }
}, { immediate: true });

// 监听认证状态变化，当用户登录后加载看板列表
watch(() => authStore.isAuthenticated, (isAuth) => {
  if (isAuth) {
    boardStore.initialize();
  }
}, { immediate: true });

// 初始化
onMounted(() => {
  boardStore.initialize();
});

// State
const showCreateBoardModal = ref(false);
const newBoardName = ref('');

// Computed
const isAuthenticated = computed(() => authStore.isAuthenticated);
const currentUser = computed(() => authStore.currentUser);

// Methods
const handleLogoClick = () => {
  // 清除当前看板状态
  boardStore.clearCurrentBoard();
};

const createNewBoard = async () => {
  if (newBoardName.value.trim()) {
    const newBoard = await boardStore.createBoard(newBoardName.value.trim());
    newBoardName.value = '';
    showCreateBoardModal.value = false;
    
    // Navigate to the new board
    if (newBoard) {
      router.push(`/board/${newBoard.id}`);
    }
  }
};

const handleLogout = () => {
  authStore.logout();
  router.push('/login');
};
</script>

<style>
@import url('https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css');
@import url('https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css');
@import url('https://fonts.loli.net/css2?family=Inter:wght@300;400;500;600;700&display=swap');
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');

:root {
  --primary-color: #3b82f6;
  --primary-hover: #2563eb;
  --sidebar-width: 260px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: 'Inter', sans-serif;
}

body {
  overflow: hidden;
}

.app-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.login-layout {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.app-layout {
  display: flex;
  width: 100%;
  height: 100%;
}

.sidebar {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  overflow: hidden;
}
</style>