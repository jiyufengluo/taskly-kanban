<template>
  <div class="kanban-list bg-gray-100 rounded-lg p-3 shadow-sm min-w-[300px] max-w-[300px] h-fit">
    <!-- List Header -->
    <div class="flex items-center justify-between mb-3 select-none">
      <div class="flex items-center gap-2 w-full">
        <!-- List Title (editable) -->
        <div
          v-if="!isEditingTitle"
          @click="startEditingTitle"
          class="font-medium text-gray-800 text-sm flex-1 cursor-pointer truncate"
        >
          {{ list.name }}
          <span class="text-xs text-gray-500 ml-1">({{ list.cards.length }})</span>
        </div>
        <input
          v-else
          ref="titleInput"
          v-model="editableTitle"
          @blur="saveListTitle"
          @keyup.enter="saveListTitle"
          @keyup.esc="cancelEditingTitle"
          class="font-medium text-gray-800 text-sm flex-1 px-2 py-1 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          type="text"
        />

        <!-- List Actions Dropdown -->
        <div class="relative">
          <button
            @click.stop="toggleDropdown"
            class="p-1 text-gray-500 hover:text-gray-800 focus:outline-none"
          >
            <i class="fas fa-ellipsis-v"></i>
          </button>
          <div
            v-if="showDropdown"
            class="absolute right-0 mt-1 w-48 bg-white rounded-md shadow-lg z-10 py-1"
            @click.stop
          >
            <button
              @click="startEditingTitle"
              class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
            >
              <i class="fas fa-pencil-alt mr-2"></i> 重命名列表
            </button>
            <button
              @click="confirmDeleteList"
              class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
            >
              <i class="fas fa-trash mr-2"></i> 删除列表
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Cards Container with Draggable -->
    <draggable
      :list="list.cards"
      :group="{ name: 'cards', pull: true, put: true }"
      item-key="id"
      ghost-class="ghost-card"
      chosen-class="chosen-card"
      animation="200"
      @change="handleDragChange"
      class="min-h-[10px] kanban-cards-container"
    >
      <template #item="{ element, index }">
        <KanbanCard
          :card="element"
          :list-id="list.id"
          @edit="openCardEditor"
        />
      </template>
    </draggable>

    <!-- Add Card Button or Form -->
    <div class="mt-2">
      <div v-if="!isAddingCard" class="add-card-button">
        <button
          @click="startAddingCard"
          class="flex items-center gap-1 w-full py-2 px-3 text-sm text-gray-600 hover:bg-gray-200 rounded-md transition-colors"
        >
          <i class="fas fa-plus"></i>
          <span>添加卡片</span>
        </button>
      </div>
      <div v-else class="add-card-form bg-white p-2 rounded shadow-sm">
        <textarea
          ref="newCardInput"
          v-model="newCardTitle"
          placeholder="请输入卡片标题..."
          class="w-full p-2 text-sm border rounded resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          rows="2"
          @keydown.enter.prevent="addNewCard"
        ></textarea>
        <div class="flex gap-2 mt-2">
          <button
            @click="addNewCard"
            class="px-3 py-1 bg-blue-600 text-white text-xs font-medium rounded hover:bg-blue-700 transition-colors"
          >
            添加卡片
          </button>
          <button
            @click="cancelAddingCard"
            class="px-3 py-1 text-gray-500 text-xs hover:text-gray-700 transition-colors"
          >
            取消
          </button>
        </div>
      </div>
    </div>

    <!-- Delete List Confirmation Modal -->
    <div
      v-if="showDeleteModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="showDeleteModal = false"
    >
      <div class="bg-white rounded-lg p-6 w-80 max-w-full">
        <h3 class="text-lg font-medium mb-4">删除列表？</h3>
        <p class="text-gray-600 mb-4">
          您确定要删除 "{{ list.name }}" 及其所有卡片吗？此操作无法撤销。
        </p>
        <div class="flex justify-end gap-2">
          <button
            @click="showDeleteModal = false"
            class="px-4 py-2 bg-gray-100 rounded-md hover:bg-gray-200"
          >
            取消
          </button>
          <button
            @click="deleteList"
            class="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600"
          >
            删除
          </button>
        </div>
      </div>
    </div>

    <!-- Card Edit/Create Modal -->
    <div
      v-if="showCardModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="closeCardModal"
    >
      <div class="bg-white rounded-lg p-6 w-96 max-w-full">
        <h3 class="text-lg font-medium mb-4">{{ editingCard ? '编辑' : '添加' }}卡片</h3>
        
        <!-- Card Title -->
        <div class="mb-3">
          <label class="block text-sm font-medium text-gray-700 mb-1">标题</label>
          <input
            v-model="cardModalData.title"
            class="w-full p-2 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="请输入卡片标题"
          />
        </div>

        <!-- Card Description -->
        <div class="mb-3">
          <label class="block text-sm font-medium text-gray-700 mb-1">描述</label>
          <textarea
            v-model="cardModalData.description"
            class="w-full p-2 border rounded text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="请输入卡片描述"
            rows="3"
          ></textarea>
        </div>

        <!-- Due Date -->
        <div class="mb-3">
          <label class="block text-sm font-medium text-gray-700 mb-1">截止日期</label>
          <input
            v-model="cardModalData.dueDate"
            type="date"
            class="w-full p-2 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <!-- Labels -->
        <div class="mb-3">
          <label class="block text-sm font-medium text-gray-700 mb-1">标签</label>
          <div class="flex flex-wrap gap-1 mb-1">
            <span
              v-for="label in cardModalData.labels"
              :key="label"
              class="text-xs px-2 py-1 rounded-full font-medium flex items-center gap-1"
              :class="getLabelClass(label)"
            >
              {{ label }}
              <button
                @click="removeLabel(label)"
                class="text-xs hover:text-red-500"
              >
                <i class="fas fa-times"></i>
              </button>
            </span>
          </div>
          <div class="flex gap-1">
            <input
              v-model="newLabel"
              class="flex-1 p-1 text-sm border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="添加标签"
              @keyup.enter="addLabel"
            />
            <button
              @click="addLabel"
              class="px-2 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
            >
              <i class="fas fa-plus"></i>
            </button>
          </div>
        </div>

        <div class="flex justify-end gap-2 mt-4">
          <button
            @click="closeCardModal"
            class="px-4 py-2 bg-gray-100 rounded-md hover:bg-gray-200 text-sm"
          >
            取消
          </button>
          <button
            @click="saveCard"
            class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
          >
            {{ editingCard ? '更新' : '创建' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue';
import draggable from 'vuedraggable';
import KanbanCard from './KanbanCard.vue';
import { useBoardStore } from '../stores/boardStore';

// Props
const props = defineProps({
  list: {
    type: Object,
    required: true
  }
});

// Store
const boardStore = useBoardStore();

// State for list title editing
const isEditingTitle = ref(false);
const editableTitle = ref('');
const titleInput = ref(null);

// State for dropdown
const showDropdown = ref(false);

// State for delete modal
const showDeleteModal = ref(false);

// State for adding a new card
const isAddingCard = ref(false);
const newCardTitle = ref('');
const newCardInput = ref(null);

// State for card modal
const showCardModal = ref(false);
const editingCard = ref(null);
const cardModalData = ref({
  title: '',
  description: '',
  dueDate: '',
  labels: []
});
const newLabel = ref('');

// Methods for list title editing
const startEditingTitle = () => {
  editableTitle.value = props.list.name;
  isEditingTitle.value = true;
  showDropdown.value = false;
  nextTick(() => {
    titleInput.value.focus();
  });
};

const saveListTitle = () => {
  if (editableTitle.value.trim()) {
    boardStore.updateList(props.list.id, { name: editableTitle.value.trim() });
  }
  isEditingTitle.value = false;
};

const cancelEditingTitle = () => {
  isEditingTitle.value = false;
};

// Methods for dropdown
const toggleDropdown = () => {
  showDropdown.value = !showDropdown.value;
};

// Methods for delete list
const confirmDeleteList = () => {
  showDropdown.value = false;
  showDeleteModal.value = true;
};

const deleteList = () => {
  boardStore.deleteList(props.list.id);
  showDeleteModal.value = false;
};

// Methods for adding a new card
const startAddingCard = () => {
  isAddingCard.value = true;
  newCardTitle.value = '';
  nextTick(() => {
    newCardInput.value.focus();
  });
};

const addNewCard = () => {
  if (newCardTitle.value.trim()) {
    boardStore.addCard(props.list.id, {
      title: newCardTitle.value.trim(),
      description: ''
    });
    newCardTitle.value = '';
    // Keep form open for adding multiple cards
    nextTick(() => {
      newCardInput.value.focus();
    });
  }
};

const cancelAddingCard = () => {
  isAddingCard.value = false;
  newCardTitle.value = '';
};

// Methods for card modal
const openCardEditor = (card) => {
  editingCard.value = card;
  cardModalData.value = {
    title: card.title,
    description: card.description || '',
    dueDate: card.dueDate || '',
    labels: [...(card.labels || [])]
  };
  showCardModal.value = true;
};

const closeCardModal = () => {
  showCardModal.value = false;
  editingCard.value = null;
  cardModalData.value = {
    title: '',
    description: '',
    dueDate: '',
    labels: []
  };
  newLabel.value = '';
};

const saveCard = () => {
  if (cardModalData.value.title.trim()) {
    if (editingCard.value) {
      // Update existing card
      boardStore.updateCard(props.list.id, editingCard.value.id, {
        title: cardModalData.value.title.trim(),
        description: cardModalData.value.description.trim(),
        dueDate: cardModalData.value.dueDate,
        labels: cardModalData.value.labels
      });
    } else {
      // Create new card
      boardStore.addCard(props.list.id, {
        title: cardModalData.value.title.trim(),
        description: cardModalData.value.description.trim(),
        dueDate: cardModalData.value.dueDate,
        labels: cardModalData.value.labels
      });
    }
    closeCardModal();
  }
};

// Label methods
const addLabel = () => {
  const label = newLabel.value.trim();
  if (label && !cardModalData.value.labels.includes(label)) {
    cardModalData.value.labels.push(label);
    newLabel.value = '';
  }
};

const removeLabel = (label) => {
  const index = cardModalData.value.labels.indexOf(label);
  if (index !== -1) {
    cardModalData.value.labels.splice(index, 1);
  }
};

// Label styles (copy from KanbanCard.vue for consistency)
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

// Handle drag events
const handleDragChange = (event) => {
  console.log('Drag change event:', event); // Debug log
  
  // Handle card movement
  if (event.added) {
    // Card was added to this list
    const { element, newIndex } = event.added;
    console.log('Card added:', element.id, 'to list:', props.list.id, 'at index:', newIndex);
    
    // Find source list by checking which list no longer has this card
    let sourceListId = null;
    const currentBoard = boardStore.getCurrentBoard;
    
    if (currentBoard) {
      // Check all lists to find where this card originally was
      for (const list of currentBoard.lists) {
        if (list.id !== props.list.id) {
          // Check if this list should have had this card but doesn't anymore
          const cardExists = list.cards.some(card => card.id === element.id);
          if (!cardExists) {
            // This might be the source list, but we need to be more careful
            // For now, let's use a different approach
          }
        }
      }
      
      // Alternative: use the element's original list_id if available
      // or find it by elimination
      sourceListId = element.originalListId || element.list_id;
      
      // If still not found, try to find by process of elimination
      if (!sourceListId) {
        for (const list of currentBoard.lists) {
          if (list.id !== props.list.id) {
            sourceListId = list.id;
            break; // Use first different list as fallback
          }
        }
      }
    }
    
    // If we have a source list, inform the store about the move
    if (sourceListId) {
      console.log('Moving card from list:', sourceListId, 'to list:', props.list.id);
      boardStore.moveCard(sourceListId, props.list.id, element.id, newIndex);
    } else {
      console.warn('Could not determine source list for card move');
    }
  } else if (event.removed) {
    // Card was removed from this list
    const { element } = event.removed;
    console.log('Card removed:', element.id, 'from list:', props.list.id);
    // Store the original list ID on the element for the destination to use
    element.originalListId = props.list.id;
  } else if (event.moved) {
    // Card was reordered within this list
    const { oldIndex, newIndex } = event.moved;
    const cardId = props.list.cards[newIndex].id;
    console.log('Card moved within list:', props.list.id, 'from index:', oldIndex, 'to index:', newIndex);
    boardStore.moveCard(props.list.id, props.list.id, cardId, newIndex);
  }
};

// Click outside handler for dropdown
const handleClickOutside = (event) => {
  if (showDropdown.value) {
    showDropdown.value = false;
  }
};

// Lifecycle hooks
onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<style scoped>
.ghost-card {
  opacity: 0.5;
  background: #f0f0f0;
  border: 1px dashed #ccc;
}

.chosen-card {
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
}

.kanban-cards-container {
  min-height: 10px;
  transition: background-color 0.2s ease;
}

.kanban-cards-container:empty {
  padding-bottom: 10px;
}
</style>