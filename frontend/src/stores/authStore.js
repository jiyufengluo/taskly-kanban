import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useToast } from 'vue-toastification';

export const useAuthStore = defineStore('auth', () => {
  const toast = useToast();
  
  // State
  const user = ref(null);
  const token = ref(localStorage.getItem('token') || null);
  const isLoading = ref(false);
  
  // API Base URL
  const API_BASE_URL = 'http://localhost:8000/api';
  
  // Computed
  const isAuthenticated = computed(() => !!token.value);
  const currentUser = computed(() => user.value);
  
  // Methods
  const setToken = (newToken) => {
    token.value = newToken;
    localStorage.setItem('token', newToken);
  };
  
  const clearToken = () => {
    token.value = null;
    localStorage.removeItem('token');
    user.value = null;
  };
  
  const login = async (email, password) => {
    isLoading.value = true;
    try {
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);
      
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '登录失败');
      }
      
      const data = await response.json();
      setToken(data.access_token);
      
      // 获取用户信息
      await fetchCurrentUser();
      
      toast.success('登录成功');
      return true;
    } catch (error) {
      toast.error(error.message || '登录失败');
      return false;
    } finally {
      isLoading.value = false;
    }
  };
  
  const register = async (userData) => {
    isLoading.value = true;
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '注册失败');
      }
      
      toast.success('注册成功，请登录');
      return true;
    } catch (error) {
      toast.error(error.message || '注册失败');
      return false;
    } finally {
      isLoading.value = false;
    }
  };
  
  const fetchCurrentUser = async () => {
    if (!token.value) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token.value}`,
        },
      });
      
      if (!response.ok) {
        throw new Error('获取用户信息失败');
      }
      
      const data = await response.json();
      user.value = data;
    } catch (error) {
      console.error('获取用户信息失败:', error);
      clearToken();
    }
  };
  
  const logout = () => {
    clearToken();
    toast.success('已退出登录');
  };
  
  // Initialize
  if (token.value) {
    fetchCurrentUser();
  }
  
  return {
    // State
    user,
    token,
    isLoading,
    
    // Computed
    isAuthenticated,
    currentUser,
    
    // Methods
    login,
    register,
    logout,
    fetchCurrentUser,
  };
});