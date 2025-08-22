<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-form">
        <!-- Logo 和标题移到表单内部 -->
        <div class="form-header">
          <div class="logo">
            <i class="fas fa-tasks"></i>
          </div>
          <h1>Taskly</h1>
          <p>实时协同看板系统</p>
        </div>
        <!-- 登录表单 -->
        <div v-if="!showRegister" class="form-section">
          <h2>登录</h2>
          <form @submit.prevent="handleLogin">
            <div class="form-group">
              <label for="email">邮箱</label>
              <input
                id="email"
                v-model="loginForm.email"
                type="email"
                required
                placeholder="请输入邮箱"
                :disabled="authStore.isLoading"
              />
            </div>
            
            <div class="form-group">
              <label for="password">密码</label>
              <input
                id="password"
                v-model="loginForm.password"
                type="password"
                required
                placeholder="请输入密码"
                :disabled="authStore.isLoading"
              />
            </div>
            
            <button
              type="submit"
              class="login-btn"
              :disabled="authStore.isLoading || !loginForm.email || !loginForm.password"
            >
              <i v-if="authStore.isLoading" class="fas fa-spinner fa-spin"></i>
              <span v-else>登录</span>
            </button>
          </form>
          
          <div class="form-footer">
            <p>还没有账户？ <a href="#" @click.prevent="showRegister = true">立即注册</a></p>
          </div>
        </div>
        
        <!-- 注册表单 -->
        <div v-else class="form-section">
          <h2>注册</h2>
          <form @submit.prevent="handleRegister">
            <div class="form-group">
              <label for="reg-email">邮箱</label>
              <input
                id="reg-email"
                v-model="registerForm.email"
                type="email"
                required
                placeholder="请输入邮箱"
                :disabled="authStore.isLoading"
              />
            </div>
            
            <div class="form-group">
              <label for="reg-username">用户名</label>
              <input
                id="reg-username"
                v-model="registerForm.username"
                type="text"
                required
                placeholder="请输入用户名"
                :disabled="authStore.isLoading"
              />
            </div>
            
            <div class="form-group">
              <label for="reg-fullname">姓名</label>
              <input
                id="reg-fullname"
                v-model="registerForm.full_name"
                type="text"
                required
                placeholder="请输入姓名"
                :disabled="authStore.isLoading"
              />
            </div>
            
            <div class="form-group">
              <label for="reg-password">密码</label>
              <input
                id="reg-password"
                v-model="registerForm.password"
                type="password"
                required
                placeholder="请输入密码"
                :disabled="authStore.isLoading"
              />
            </div>
            
            <button
              type="submit"
              class="login-btn"
              :disabled="authStore.isLoading || !isRegisterFormValid"
            >
              <i v-if="authStore.isLoading" class="fas fa-spinner fa-spin"></i>
              <span v-else>注册</span>
            </button>
          </form>
          
          <div class="form-footer">
            <p>已有账户？ <a href="#" @click.prevent="showRegister = false">立即登录</a></p>
          </div>
        </div>
        
        <!-- 演示账户信息移到表单底部 -->
        <div class="demo-info">
          <div class="demo-accounts">
            <div class="demo-account">
              <strong>管理员:</strong> admin@taskly.com / admin123
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/authStore';
import { useToast } from 'vue-toastification';

const router = useRouter();
const authStore = useAuthStore();
const toast = useToast();

// 表单状态
const showRegister = ref(false);
const loginForm = ref({
  email: '',
  password: ''
});
const registerForm = ref({
  email: '',
  username: '',
  full_name: '',
  password: ''
});

// 计算属性
const isRegisterFormValid = computed(() => {
  return registerForm.value.email &&
         registerForm.value.username &&
         registerForm.value.full_name &&
         registerForm.value.password;
});

// 方法
const handleLogin = async () => {
  const success = await authStore.login(loginForm.value.email, loginForm.value.password);
  if (success) {
    router.push('/');
  }
};

const handleRegister = async () => {
  const success = await authStore.register(registerForm.value);
  if (success) {
    showRegister.value = false;
    loginForm.value.email = registerForm.value.email;
    loginForm.value.password = registerForm.value.password;
    registerForm.value = {
      email: '',
      username: '',
      full_name: '',
      password: ''
    };
  }
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Lato:wght@400;500;600;700&display=swap');

.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  font-family: 'Inter', 'Lato', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.login-card {
  background: transparent;
  border-radius: 16px;
  background: linear-gradient(135deg, #F4F6FF 0%, #FFFFFF 100%);
  box-shadow: 0px 10px 30px rgba(0, 0, 0, 0.07);
  width: 420px;
  height: auto;
  overflow: hidden;
}

.login-form {
  padding: 40px;
}

.form-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo {
  width: 48px;
  height: 48px;
  background: #5468FF;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  font-size: 20px;
  color: white;
}

.form-header h1 {
  font-size: 24px;
  margin-bottom: 8px;
  color: #1A202C;
  font-weight: 700;
  line-height: 1.2;
}

.form-header p {
  color: #4A5568;
  font-size: 14px;
  margin: 0;
  margin-bottom: 32px;
  font-weight: 400;
  line-height: 1.4;
}

.form-section h2 {
  color: #1A202C;
  margin-bottom: 24px;
  text-align: center;
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.form-group {
  margin-bottom: 8px;
}

.form-group:last-of-type {
  margin-bottom: 24px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #4A5568;
  font-weight: 500;
  font-size: 14px;
  line-height: 1.4;
}

.form-group input {
  width: 100%;
  height: 48px;
  padding: 0 16px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 400;
  transition: all 0.2s ease;
  background: #FFFFFF;
  box-sizing: border-box;
  color: #1A202C;
  line-height: 1.5;
}

.form-group input::placeholder {
  color: #A0AEC0;
  font-weight: 400;
}

.form-group input:focus {
  outline: none;
  border-color: #5468FF;
  box-shadow: 0 0 0 3px rgba(84, 104, 255, 0.1);
}

.form-group input:disabled {
  background-color: #F9FAFB;
  cursor: not-allowed;
  color: #6B7280;
}

.login-btn {
  width: 100%;
  height: 48px;
  background: #5468FF;
  color: #FFFFFF;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 20px;
  line-height: 1.5;
}

.login-btn:hover:not(:disabled) {
  background: #6374FF;
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.form-footer {
  text-align: center;
  margin-bottom: 32px;
}

.form-footer p {
  font-size: 14px;
  color: #4A5568;
  margin: 0;
  line-height: 1.4;
}

.form-footer a {
  color: #5468FF;
  text-decoration: none;
  font-weight: 400;
  transition: all 0.2s ease;
}

.form-footer a:hover {
  text-decoration: underline;
}

.demo-info {
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid #E2E8F0;
}

.demo-accounts {
  font-size: 12px;
  color: #718096;
  line-height: 1.4;
}

.demo-account {
  margin-bottom: 4px;
}

.demo-account strong {
  color: #718096;
  font-weight: 400;
}

@media (max-width: 480px) {
  .login-container {
    padding: 16px;
  }
  
  .login-card {
    width: 90%;
    max-width: 90%;
    height: auto;
  }
  
  .login-form {
    padding: 32px;
  }
}
</style>