import { createApp } from 'vue';
import { createPinia } from 'pinia';
import { createRouter, createWebHashHistory } from 'vue-router';
import Toast from 'vue-toastification';
import 'vue-toastification/dist/index.css';
import App from './App.vue';
import { useAuthStore } from './stores/authStore';

// 导入视图组件
const BoardView = () => import('./views/BoardView.vue');
const DashboardView = () => import('./views/DashboardView.vue');
const SettingsView = () => import('./views/SettingsView.vue');
const HomeView = () => import('./views/HomeView.vue');
const LoginView = () => import('./views/LoginView.vue');

// 认证守卫
const requireAuth = (to, from, next) => {
  const authStore = useAuthStore();
  if (!authStore.isAuthenticated) {
    next('/login');
  } else {
    next();
  }
};

// 创建路由实例
const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      beforeEnter: requireAuth
    },
    {
      path: '/board/:id',
      name: 'board',
      component: BoardView,
      beforeEnter: requireAuth
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView,
      beforeEnter: requireAuth
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView,
      beforeEnter: requireAuth
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    }
  ]
});

// 创建Pinia存储
const pinia = createPinia();

// 创建Vue应用
const app = createApp(App);

// 配置Vue Toast通知
const toastOptions = {
  position: 'top-right',
  timeout: 3000,
  closeOnClick: true,
  pauseOnFocusLoss: true,
  pauseOnHover: true,
  draggable: true,
  draggablePercent: 0.6,
  showCloseButtonOnHover: false,
  hideProgressBar: false,
  closeButton: 'button',
  icon: true,
  rtl: false
};

// 使用插件
app.use(router);
app.use(pinia);
app.use(Toast, toastOptions);

// 挂载应用
app.mount('#app');