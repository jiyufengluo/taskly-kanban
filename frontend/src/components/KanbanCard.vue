<template>
  <div
    class="kanban-card transition-all duration-300 bg-white rounded-lg shadow-md hover:shadow-lg mb-2 cursor-pointer select-none p-3"
    :class="{ 'border-l-4 border-blue-500': isHighPriority }"
    @click.stop="openCardDetails"
  >
    <!-- Card Labels -->
    <div class="flex flex-wrap gap-1 mb-2" v-if="card.labels && card.labels.length">
      <span
        v-for="label in card.labels"
        :key="label"
        class="text-xs px-2 py-1 rounded-full font-medium"
        :class="getLabelClass(label)"
      >
        {{ label }}
      </span>
    </div>

    <!-- Card Title -->
    <h3 class="text-sm font-medium text-gray-800 mb-2 line-clamp-2">{{ card.title }}</h3>

    <!-- Card Description Preview (if exists) -->
    <p 
      v-if="card.description" 
      class="text-xs text-gray-600 mb-2 line-clamp-2"
    >
      {{ card.description }}
    </p>

    <!-- Card Footer -->
    <div class="flex items-center justify-between mt-2 text-xs text-gray-500">
      <!-- Due Date -->
      <div v-if="card.dueDate" class="flex items-center">
        <i class="fas fa-calendar-alt mr-1"></i>
        <span :class="{ 'text-red-500': isOverdue, 'text-orange-500': isAlmostDue }">
          {{ formattedDueDate }}
        </span>
      </div>
      <div v-else></div>

      <!-- Action Buttons -->
      <div class="flex gap-2">
        <!-- Edit Button -->
        <button 
          @click.stop="editCard" 
          class="text-gray-400 hover:text-blue-500 transition-colors"
          title="编辑卡片"
        >
          <i class="fas fa-pencil-alt"></i>
        </button>
        <!-- Delete Button -->
        <button 
          @click.stop="confirmDelete" 
          class="text-gray-400 hover:text-red-500 transition-colors"
          title="删除卡片"
        >
          <i class="fas fa-trash-alt"></i>
        </button>
      </div>
    </div>

    <!-- Assigned Users -->
    <div class="flex mt-2 -space-x-2" v-if="card.assignedUsers && card.assignedUsers.length">
      <div 
        v-for="(user, index) in card.assignedUsers.slice(0, 3)" 
        :key="index"
        class="w-6 h-6 rounded-full bg-gray-200 border border-white flex items-center justify-center text-xs font-medium"
        :title="user.name || 'User'"
      >
        {{ getUserInitials(user) }}
      </div>
      <div 
        v-if="card.assignedUsers.length > 3"
        class="w-6 h-6 rounded-full bg-gray-100 border border-white flex items-center justify-center text-xs"
        :title="`${card.assignedUsers.length - 3} more`"
      >
        +{{ card.assignedUsers.length - 3 }}
      </div>
    </div>

    <!-- Delete Confirmation Modal (would use Element Plus in real implementation) -->
    <div v-if="showDeleteModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="showDeleteModal = false">
      <div class="bg-white rounded-lg p-6 w-80 max-w-full">
        <h3 class="text-lg font-medium mb-4">删除卡片？</h3>
        <p class="text-gray-600 mb-4">您确定要删除 "{{ card.title }}" 吗？此操作无法撤销。</p>
        <div class="flex justify-end gap-2">
          <button @click="showDeleteModal = false" class="px-4 py-2 bg-gray-100 rounded-md hover:bg-gray-200">取消</button>
          <button @click="deleteCard" class="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600">删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useBoardStore } from '../stores/boardStore';

// Props
const props = defineProps({
  card: {
    type: Object,
    required: true
  },
  listId: {
    type: String,
    required: true
  }
});

// Emits
const emit = defineEmits(['edit']);

// Store
const boardStore = useBoardStore();

// State
const showDeleteModal = ref(false);

// Computed
const formattedDueDate = computed(() => {
  if (!props.card.dueDate) return '';
  
  const date = new Date(props.card.dueDate);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);
  
  if (date.toDateString() === today.toDateString()) {
    return 'Today';
  } else if (date.toDateString() === tomorrow.toDateString()) {
    return 'Tomorrow';
  } else {
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    });
  }
});

const isOverdue = computed(() => {
  if (!props.card.dueDate) return false;
  const dueDate = new Date(props.card.dueDate);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return dueDate < today;
});

const isAlmostDue = computed(() => {
  if (!props.card.dueDate) return false;
  if (isOverdue.value) return false;
  
  const dueDate = new Date(props.card.dueDate);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const diff = dueDate.getTime() - today.getTime();
  const daysDiff = diff / (1000 * 3600 * 24);
  
  return daysDiff <= 2; // If due date is within 2 days
});

const isHighPriority = computed(() => {
  if (!props.card.labels) return false;
  return props.card.labels.some(label => 
    ['urgent', 'high', 'important'].includes(label.toLowerCase())
  );
});

// Methods
const getLabelClass = (label) => {
  // Map label names to TailwindCSS classes
  const labelMap = {
    'design': 'bg-purple-100 text-purple-800',
    'research': 'bg-blue-100 text-blue-800',
    'technical': 'bg-green-100 text-green-800',
    'bug': 'bg-red-100 text-red-800',
    'setup': 'bg-gray-100 text-gray-800',
    'meeting': 'bg-yellow-100 text-yellow-800',
    'urgent': 'bg-red-100 text-red-800',
    'high': 'bg-orange-100 text-orange-800',
    'important': 'bg-yellow-100 text-yellow-800',
  };
  
  // Return mapped class or default
  return labelMap[label.toLowerCase()] || 'bg-gray-100 text-gray-800';
};

const getUserInitials = (user) => {
  if (!user || !user.name) return '?';
  return user.name.split(' ').map(name => name[0]).join('').toUpperCase().substring(0, 2);
};

const openCardDetails = () => {
  // This would typically open a modal or navigate to a details page
  console.log('Opening card details for:', props.card.id);
  // Placeholder for future implementation
};

const editCard = () => {
  emit('edit', props.card);
};

const confirmDelete = (e) => {
  e.stopPropagation();
  showDeleteModal.value = true;
};

const deleteCard = () => {
  boardStore.deleteCard(props.listId, props.card.id);
  showDeleteModal.value = false;
};
</script>

<style scoped>
.kanban-card {
  min-height: 80px;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>