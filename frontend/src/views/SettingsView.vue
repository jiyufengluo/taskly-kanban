<template>
  <div class="settings-view h-screen overflow-y-auto bg-gray-50">
    <div class="container mx-auto px-4 py-8">
      <!-- Settings Header -->
      <div class="mb-8">
        <h1 class="text-2xl font-bold text-gray-800 mb-2">设置</h1>
        <p class="text-gray-600">自定义您的 Taskly 体验</p>
      </div>
      
      <!-- Settings Content -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Sidebar Navigation -->
        <div class="lg:col-span-1">
          <div class="bg-white rounded-lg shadow-sm p-4">
            <ul class="space-y-1">
              <li v-for="(section, index) in settingsSections" :key="index">
                <button 
                  @click="activeSection = section.id"
                  class="w-full px-4 py-2 rounded-md text-left transition-colors"
                  :class="activeSection === section.id 
                    ? 'bg-blue-50 text-blue-600 font-medium' 
                    : 'text-gray-700 hover:bg-gray-50'"
                >
                  <i :class="['mr-3', section.icon]"></i>
                  {{ section.name }}
                </button>
              </li>
            </ul>
          </div>
        </div>
        
        <!-- Settings Main Content -->
        <div class="lg:col-span-2">
          <div class="bg-white rounded-lg shadow-sm p-6">
            <!-- Profile Settings -->
            <div v-if="activeSection === 'profile'" class="space-y-6">
              <h2 class="text-xl font-medium text-gray-800 mb-4">个人资料设置</h2>
              
              <!-- Profile Picture -->
              <div class="flex items-center space-x-4">
                <div class="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center text-xl font-medium">
                  JD
                </div>
                <div>
                  <button class="px-3 py-2 bg-blue-50 text-blue-600 rounded-md hover:bg-blue-100 transition-colors text-sm">
                    更换头像
                  </button>
                </div>
              </div>
              
              <!-- Profile Form -->
              <form @submit.prevent="saveProfile" class="space-y-4">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">名</label>
                    <input
                      v-model="profile.firstName"
                      type="text"
                      class="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">姓</label>
                    <input
                      v-model="profile.lastName"
                      type="text"
                      class="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
                  <input
                    v-model="profile.email"
                    type="email"
                    class="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">职位</label>
                  <input
                    v-model="profile.jobTitle"
                    type="text"
                    class="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div class="pt-2">
                  <button
                    type="submit"
                    class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    保存更改
                  </button>
                </div>
              </form>
            </div>
            
            <!-- Appearance Settings -->
            <div v-else-if="activeSection === 'appearance'" class="space-y-6">
              <h2 class="text-xl font-medium text-gray-800 mb-4">外观</h2>
              
              <!-- Theme Selection -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-3">主题</label>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div
                    v-for="(theme, index) in themes"
                    :key="index"
                    @click="appearance.theme = theme.id"
                    class="theme-option border rounded-lg p-3 cursor-pointer"
                    :class="appearance.theme === theme.id ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-200'"
                  >
                    <div :class="['h-10 rounded-md mb-2', theme.previewClass]"></div>
                    <div class="text-sm font-medium">{{ theme.name }}</div>
                  </div>
                </div>
              </div>
              
              <!-- Card Style -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-3">卡片样式</label>
                <div class="space-y-2">
                  <label class="flex items-center cursor-pointer">
                    <input
                      type="radio"
                      name="cardStyle"
                      value="default"
                      v-model="appearance.cardStyle"
                      class="mr-2"
                    />
                    <span>默认</span>
                  </label>
                  <label class="flex items-center cursor-pointer">
                    <input
                      type="radio"
                      name="cardStyle"
                      value="compact"
                      v-model="appearance.cardStyle"
                      class="mr-2"
                    />
                    <span>紧凑</span>
                  </label>
                  <label class="flex items-center cursor-pointer">
                    <input
                      type="radio"
                      name="cardStyle"
                      value="detailed"
                      v-model="appearance.cardStyle"
                      class="mr-2"
                    />
                    <span>详细</span>
                  </label>
                </div>
              </div>
              
              <div class="pt-2">
                <button
                  @click="saveAppearance"
                  class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  保存外观设置
                </button>
              </div>
            </div>
            
            <!-- Notifications Settings -->
            <div v-else-if="activeSection === 'notifications'" class="space-y-6">
              <h2 class="text-xl font-medium text-gray-800 mb-4">通知</h2>
              
              <div class="space-y-4">
                <div v-for="(setting, index) in notificationSettings" :key="index" class="flex items-center justify-between py-2 border-b border-gray-100">
                  <div>
                    <h3 class="font-medium text-gray-800">{{ setting.name }}</h3>
                    <p class="text-sm text-gray-500">{{ setting.description }}</p>
                  </div>
                  <label class="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" v-model="setting.enabled" class="sr-only peer" />
                    <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>
              
              <div class="pt-2">
                <button
                  @click="saveNotifications"
                  class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  保存通知设置
                </button>
              </div>
            </div>
            
            <!-- Security Settings -->
            <div v-else-if="activeSection === 'security'" class="space-y-6">
              <h2 class="text-xl font-medium text-gray-800 mb-4">安全</h2>
              
              <!-- Change Password -->
              <div class="mb-6">
                <h3 class="font-medium text-gray-800 mb-2">修改密码</h3>
                <form @submit.prevent="changePassword" class="space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">当前密码</label>
                    <input
                      v-model="security.currentPassword"
                      type="password"
                      class="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">新密码</label>
                    <input
                      v-model="security.newPassword"
                      type="password"
                      class="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">确认新密码</label>
                    <input
                      v-model="security.confirmPassword"
                      type="password"
                      class="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div class="pt-2">
                    <button
                      type="submit"
                      class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    >
                      修改密码
                    </button>
                  </div>
                </form>
              </div>
              
              <!-- Two-Factor Authentication -->
              <div class="py-4 border-t border-gray-100">
                <div class="flex items-center justify-between">
                  <div>
                    <h3 class="font-medium text-gray-800">双因素认证</h3>
                    <p class="text-sm text-gray-500">为您的账户添加额外的安全保护层</p>
                  </div>
                  <label class="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" v-model="security.twoFactorEnabled" class="sr-only peer" />
                    <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>
              
              <!-- Session Management -->
              <div class="py-4 border-t border-gray-100">
                <h3 class="font-medium text-gray-800 mb-2">活动会话</h3>
                <div v-for="(session, index) in security.activeSessions" :key="index" class="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0">
                  <div>
                    <div class="font-medium">{{ session.device }}</div>
                    <div class="text-sm text-gray-500">{{ session.location }} · {{ session.lastActive }}</div>
                  </div>
                  <button @click="terminateSession(session.id)" class="text-sm text-red-600 hover:text-red-800">
                    注销
                  </button>
                </div>
                <div class="mt-4">
                  <button 
                    @click="logoutAllSessions" 
                    class="text-sm text-red-600 hover:text-red-800 flex items-center"
                  >
                    <i class="fas fa-sign-out-alt mr-1"></i> 从所有设备注销
                  </button>
                </div>
              </div>
            </div>
            
            <!-- Integrations Settings -->
            <div v-else-if="activeSection === 'integrations'" class="space-y-6">
              <h2 class="text-xl font-medium text-gray-800 mb-4">Integrations</h2>
              
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div v-for="(integration, index) in integrations" :key="index" class="border rounded-lg p-4 relative">
                  <div class="flex items-center mb-3">
                    <div class="w-10 h-10 rounded-md bg-gray-100 flex items-center justify-center text-xl">
                      <i :class="integration.icon"></i>
                    </div>
                    <div class="ml-3">
                      <h3 class="font-medium">{{ integration.name }}</h3>
                      <p class="text-xs text-gray-500">{{ integration.status }}</p>
                    </div>
                  </div>
                  <p class="text-sm text-gray-600 mb-3">{{ integration.description }}</p>
                  <button 
                    :class="[
                      'text-sm px-3 py-1 rounded-md',
                      integration.connected ? 'bg-gray-100 text-gray-800' : 'bg-blue-600 text-white'
                    ]"
                    @click="toggleIntegration(integration)"
                  >
                    {{ integration.connected ? 'Disconnect' : 'Connect' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useToast } from 'vue-toastification';

const toast = useToast();

// Settings sections
const settingsSections = [
  { id: 'profile', name: '个人资料', icon: 'fas fa-user' },
  { id: 'appearance', name: '外观', icon: 'fas fa-palette' },
  { id: 'notifications', name: '通知', icon: 'fas fa-bell' },
  { id: 'security', name: '安全', icon: 'fas fa-shield-alt' },
  { id: 'integrations', name: '集成', icon: 'fas fa-plug' }
];

// Active section
const activeSection = ref('profile');

// Profile settings
const profile = ref({
  firstName: 'John',
  lastName: 'Doe',
  email: 'john@example.com',
  jobTitle: 'Project Manager'
});

// Appearance settings
const appearance = ref({
  theme: 'light',
  cardStyle: 'default'
});

// Available themes
const themes = [
  { id: 'light', name: '浅色', previewClass: 'bg-white border border-gray-200' },
  { id: 'dark', name: '深色', previewClass: 'bg-gray-800' },
  { id: 'blue', name: '蓝色', previewClass: 'bg-blue-700' },
  { id: 'green', name: '绿色', previewClass: 'bg-green-600' }
];

// Notification settings
const notificationSettings = ref([
  { 
    name: '卡片分配',
    description: '当有卡片分配给我时通知我',
    enabled: true
  },
  { 
    name: '截止日期',
    description: '发送即将到期的截止日期提醒',
    enabled: true
  },
  { 
    name: '看板变更',
    description: '当我参与的看板发生变更时通知我',
    enabled: false
  },
  { 
    name: '评论',
    description: '当有人评论我的卡片时通知我',
    enabled: true
  },
  { 
    name: '邮件通知',
    description: '除了应用内通知外，还发送邮件通知',
    enabled: false
  }
]);

// Security settings
const security = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
  twoFactorEnabled: false,
  activeSessions: [
    { 
      id: '1', 
      device: 'Windows 上的 Chrome',
      location: '旧金山，加利福尼亚',
      lastActive: '1小时前',
      current: true
    },
    { 
      id: '2', 
      device: 'iPhone 上的 Safari',
      location: '旧金山，加利福尼亚',
      lastActive: '2天前',
      current: false
    }
  ]
});

// Integrations
const integrations = ref([
  {
    id: 'github',
    name: 'GitHub',
    icon: 'fab fa-github',
    description: '链接您的 GitHub 仓库，直接在 Taskly 中跟踪问题。',
    connected: true,
    status: '已连接'
  },
  {
    id: 'slack',
    name: 'Slack',
    icon: 'fab fa-slack',
    description: '向 Slack 频道发送通知，并从消息创建卡片。',
    connected: false,
    status: '未连接'
  },
  {
    id: 'drive',
    name: 'Google Drive',
    icon: 'fab fa-google-drive',
    description: '将 Google Drive 文件附加到您的卡片和项目中。',
    connected: false,
    status: '未连接'
  },
  {
    id: 'zoom',
    name: 'Zoom',
    icon: 'fas fa-video',
    description: '直接从您的 Taskly 卡片启动 Zoom 会议。',
    connected: false,
    status: '未连接'
  }
]);

// Methods
const saveProfile = () => {
  // In a real app, this would call an API to update the profile
  toast.success('个人资料更新成功');
};

const saveAppearance = () => {
  // In a real app, this would update the application theme and save the settings
  toast.success('外观设置已保存');
};

const saveNotifications = () => {
  // In a real app, this would update notification preferences
  toast.success('通知设置已更新');
};

const changePassword = () => {
  // Validate passwords
  if (!security.value.currentPassword) {
    toast.error('请输入当前密码');
    return;
  }
  
  if (!security.value.newPassword) {
    toast.error('请输入新密码');
    return;
  }
  
  if (security.value.newPassword !== security.value.confirmPassword) {
    toast.error('新密码不匹配');
    return;
  }
  
  // In a real app, this would call an API to change the password
  toast.success('密码修改成功');
  
  // Clear password fields
  security.value.currentPassword = '';
  security.value.newPassword = '';
  security.value.confirmPassword = '';
};

const terminateSession = (sessionId) => {
  // In a real app, this would call an API to terminate the session
  security.value.activeSessions = security.value.activeSessions.filter(s => s.id !== sessionId);
  toast.success('会话已终止');
};

const logoutAllSessions = () => {
  // In a real app, this would call an API to logout of all sessions except the current one
  security.value.activeSessions = security.value.activeSessions.filter(s => s.current);
  toast.success('已从所有其他设备注销');
};

const toggleIntegration = (integration) => {
  integration.connected = !integration.connected;
  integration.status = integration.connected ? '已连接' : '未连接';
  
  if (integration.connected) {
    toast.success(`已连接到 ${integration.name}`);
  } else {
    toast.info(`已断开与 ${integration.name} 的连接`);
  }
};
</script>

<style scoped>
.theme-option {
  transition: all 0.2s ease;
}

.theme-option:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}
</style>