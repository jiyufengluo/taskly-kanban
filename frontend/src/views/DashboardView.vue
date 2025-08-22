<template>
  <div class="dashboard-container p-6 h-full overflow-y-auto">
    <!-- Dashboard Header -->
    <div class="dashboard-header mb-6">
      <h1 class="text-2xl font-bold text-gray-800">仪表板</h1>
      <p class="text-gray-600 mt-1">欢迎回来！这里是您的任务和项目概览</p>
    </div> 

    <!-- Stats Overview Cards -->
    <div class="stats-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
      <div v-for="(stat, index) in statCards" :key="index" 
           class="stat-card bg-white rounded-lg shadow p-5 animate__animated animate__fadeIn"
           :style="{ animationDelay: `${index * 0.1}s` }">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-sm font-medium text-gray-500">{{ stat.title }}</h3>
            <p class="text-2xl font-bold text-gray-900 mt-1">{{ stat.value }}</p>
          </div>
          <div :class="`icon-bg-${stat.color} w-10 h-10 rounded-full flex items-center justify-center`">
            <i :class="`fas ${stat.icon} text-white`"></i>
          </div>
        </div>
        <div class="mt-2 flex items-center text-sm">
          <span :class="`text-${stat.trend === 'up' ? 'green' : 'red'}-500 font-medium`">
            <i :class="`fas fa-arrow-${stat.trend} mr-1`"></i>{{ stat.change }}%
          </span>
          <span class="text-gray-500 ml-1">与上月相比</span>
        </div>
      </div>
    </div>

    <!-- Main Dashboard Content -->
    <div class="dashboard-content grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Tasks Progress -->
      <div class="lg:col-span-2">
        <div class="bg-white rounded-lg shadow p-5 mb-6">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-lg font-semibold text-gray-800">任务进度</h2>
            <div class="flex items-center">
              <button class="text-gray-500 hover:text-gray-700">
                <i class="fas fa-filter mr-1"></i> 筛选
              </button>
              <div class="border-r mx-3 h-5"></div>
              <div class="relative">
                <button class="text-gray-500 hover:text-gray-700">
                  本周 <i class="fas fa-chevron-down ml-1"></i>
                </button>
              </div>
            </div>
          </div>
          
          <div class="task-progress space-y-4">
            <div v-for="task in tasks" :key="task.id" class="task-item">
              <div class="flex justify-between items-center mb-1">
                <div class="flex items-center">
                  <span class="font-medium text-gray-800">{{ task.name }}</span>
                  <span :class="`status-badge ml-2 px-2 py-1 text-xs rounded-full ${getStatusClass(task.status)}`">
                    {{ task.status }}
                  </span>
                </div>
                <span class="text-sm text-gray-500">{{ task.completion }}%</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-2">
                <div class="h-2 rounded-full" 
                     :class="getProgressColor(task.status)"
                     :style="`width: ${task.completion}%`"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent Activity -->
        <div class="bg-white rounded-lg shadow p-5">
          <h2 class="text-lg font-semibold text-gray-800 mb-4">最近活动</h2>
          
          <div class="activity-timeline space-y-4">
            <div v-for="(activity, index) in activities" :key="index" class="activity-item flex">
              <div class="activity-icon mr-3 mt-1">
                <div :class="`w-8 h-8 rounded-full flex items-center justify-center ${getActivityIconClass(activity.type)}`">
                  <i :class="`fas ${getActivityIcon(activity.type)} text-white`"></i>
                </div>
              </div>
              <div class="activity-content flex-grow">
                <p class="text-gray-800"><span class="font-medium">{{ activity.user }}</span> {{ activity.action }}</p>
                <p class="text-sm text-gray-500">{{ activity.time }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Sidebar Content -->
      <div class="dashboard-sidebar">
        <!-- Calendar -->
        <div class="bg-white rounded-lg shadow p-5 mb-6">
          <h2 class="text-lg font-semibold text-gray-800 mb-4">日历</h2>
          <div class="calendar-widget">
            <div class="calendar-header flex justify-between items-center mb-4">
              <button class="text-gray-500 hover:text-gray-700">
                <i class="fas fa-chevron-left"></i>
              </button>
              <h3 class="text-md font-medium">August 2025</h3>
              <button class="text-gray-500 hover:text-gray-700">
                <i class="fas fa-chevron-right"></i>
              </button>
            </div>

            <div class="calendar-days grid grid-cols-7 gap-1 text-center">
              <div v-for="day in ['S', 'M', 'T', 'W', 'T', 'F', 'S']" :key="day" class="text-xs text-gray-500 font-medium py-1">
                {{ day }}
              </div>
              <div v-for="date in calendarDates" :key="date.value" 
                   :class="`text-sm py-2 rounded-full ${date.isToday ? 'bg-blue-600 text-white' : date.isCurrentMonth ? 'hover:bg-gray-100 cursor-pointer' : 'text-gray-400'}`">
                {{ date.value }}
              </div>
            </div>
          </div>
        </div>

        <!-- Upcoming Deadlines -->
        <div class="bg-white rounded-lg shadow p-5">
          <h2 class="text-lg font-semibold text-gray-800 mb-4">Upcoming Deadlines</h2>
          
          <div class="deadlines-list space-y-3">
            <div v-for="(deadline, index) in deadlines" :key="index" class="deadline-item p-3 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors">
              <h4 class="font-medium text-gray-800">{{ deadline.task }}</h4>
              <div class="flex items-center justify-between mt-2">
                <span class="text-sm text-gray-500">
                  <i class="far fa-calendar-alt mr-1"></i> {{ deadline.date }}
                </span>
                <span :class="`text-sm ${deadline.daysLeft <= 1 ? 'text-red-500' : deadline.daysLeft <= 3 ? 'text-orange-500' : 'text-green-500'}`">
                  {{ deadline.daysLeft }} days left
                </span>
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

// Statistics Cards Data
const statCards = ref([
  {
    title: 'Total Tasks',
    value: '248',
    icon: 'fa-tasks',
    color: 'blue',
    trend: 'up',
    change: '12'
  },
  {
    title: 'Completed',
    value: '184',
    icon: 'fa-check-circle',
    color: 'green',
    trend: 'up',
    change: '18'
  },
  {
    title: 'In Progress',
    value: '42',
    icon: 'fa-spinner',
    color: 'orange',
    trend: 'down',
    change: '5'
  },
  {
    title: 'Overdue',
    value: '22',
    icon: 'fa-exclamation-circle',
    color: 'red',
    trend: 'up',
    change: '8'
  }
]);

// Tasks Data
const tasks = ref([
  {
    id: 1,
    name: 'Website Redesign',
    status: 'In Progress',
    completion: 65
  },
  {
    id: 2,
    name: 'Mobile App Development',
    status: 'Completed',
    completion: 100
  },
  {
    id: 3,
    name: 'Q3 Financial Report',
    status: 'On Hold',
    completion: 30
  },
  {
    id: 4,
    name: 'Marketing Campaign',
    status: 'Overdue',
    completion: 45
  },
  {
    id: 5,
    name: 'Product Launch Preparation',
    status: 'Not Started',
    completion: 0
  }
]);

// Activities Data
const activities = ref([
  {
    user: 'You',
    action: 'completed the task "Design homepage mockup"',
    time: '2 hours ago',
    type: 'complete'
  },
  {
    user: 'John Doe',
    action: 'commented on "API Integration"',
    time: '4 hours ago',
    type: 'comment'
  },
  {
    user: 'Sarah Smith',
    action: 'created a new task "Fix navigation bugs"',
    time: 'Yesterday at 4:30 PM',
    type: 'create'
  },
  {
    user: 'Alex Turner',
    action: 'assigned you to "Database optimization"',
    time: 'Yesterday at 2:15 PM',
    type: 'assign'
  }
]);

// Calendar Data
const calendarDates = ref([
  // Previous month
  ...Array.from({ length: 4 }, (_, i) => ({ value: 28 + i, isCurrentMonth: false, isToday: false })),
  
  // Current month
  ...Array.from({ length: 31 }, (_, i) => ({ 
    value: i + 1, 
    isCurrentMonth: true, 
    isToday: i + 1 === 13 // assuming today is the 13th
  })),
  
  // Next month
  ...Array.from({ length: 7 }, (_, i) => ({ value: i + 1, isCurrentMonth: false, isToday: false }))
]);

// Deadlines Data
const deadlines = ref([
  {
    task: 'Client Presentation',
    date: 'Aug 16, 2025',
    daysLeft: 3
  },
  {
    task: 'Project Milestone Review',
    date: 'Aug 18, 2025',
    daysLeft: 5
  },
  {
    task: 'Budget Approval',
    date: 'Aug 14, 2025',
    daysLeft: 1
  },
  {
    task: 'Team Performance Evaluation',
    date: 'Aug 25, 2025',
    daysLeft: 12
  }
]);

// Helper functions
const getStatusClass = (status) => {
  switch (status) {
    case 'Completed': return 'bg-green-100 text-green-800';
    case 'In Progress': return 'bg-blue-100 text-blue-800';
    case 'On Hold': return 'bg-yellow-100 text-yellow-800';
    case 'Overdue': return 'bg-red-100 text-red-800';
    case 'Not Started': return 'bg-gray-100 text-gray-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

const getProgressColor = (status) => {
  switch (status) {
    case 'Completed': return 'bg-green-500';
    case 'In Progress': return 'bg-blue-500';
    case 'On Hold': return 'bg-yellow-500';
    case 'Overdue': return 'bg-red-500';
    case 'Not Started': return 'bg-gray-300';
    default: return 'bg-gray-300';
  }
};

const getActivityIcon = (type) => {
  switch (type) {
    case 'complete': return 'fa-check';
    case 'comment': return 'fa-comment';
    case 'create': return 'fa-plus';
    case 'assign': return 'fa-user';
    default: return 'fa-circle';
  }
};

const getActivityIconClass = (type) => {
  switch (type) {
    case 'complete': return 'bg-green-500';
    case 'comment': return 'bg-blue-500';
    case 'create': return 'bg-purple-500';
    case 'assign': return 'bg-orange-500';
    default: return 'bg-gray-500';
  }
};
</script>

<style scoped>
.icon-bg-blue {
  background-color: var(--primary-color, #3b82f6);
}

.icon-bg-green {
  background-color: #10b981;
}

.icon-bg-orange {
  background-color: #f59e0b;
}

.icon-bg-red {
  background-color: #ef4444;
}

.dashboard-container {
  background-color: #f9fafb;
}

.calendar-days {
  min-height: 200px;
}
</style>