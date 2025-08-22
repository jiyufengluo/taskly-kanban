import { useAuthStore } from '../stores/authStore';

const API_BASE_URL = 'http://localhost:8000/api';

class ApiService {
  constructor() {
    // Don't initialize authStore in constructor
  }
  
  // Helper method to get auth store
  getAuthStore() {
    return useAuthStore();
  }
  
  // Helper method to get auth headers
  getAuthHeaders() {
    const authStore = this.getAuthStore();
    const token = authStore.token;
    return token ? {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    } : {
      'Content-Type': 'application/json',
    };
  }
  
  // Generic request method
  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
      ...options,
      headers: {
        ...this.getAuthHeaders(),
        ...options.headers,
      },
    };
    
    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API请求失败:', error);
      throw error;
    }
  }
  
  // Project API
  async getProjects() {
    return this.request('/projects/');
  }
  
  async createProject(projectData) {
    return this.request('/projects/', {
      method: 'POST',
      body: JSON.stringify(projectData),
    });
  }
  
  async getProject(projectId) {
    return this.request(`/projects/${projectId}`);
  }
  
  async updateProject(projectId, projectData) {
    return this.request(`/projects/${projectId}`, {
      method: 'PUT',
      body: JSON.stringify(projectData),
    });
  }
  
  async deleteProject(projectId) {
    return this.request(`/projects/${projectId}`, {
      method: 'DELETE',
    });
  }
  
  // List API - 通过获取项目看板来获取列表
  async getLists(projectId) {
    // 先获取项目的看板
    const boards = await this.request(`/boards/project/${projectId}`);
    if (boards.length === 0) {
      return [];
    }
    // 获取第一个看板的详情（包含列表）
    const boardDetail = await this.request(`/boards/${boards[0].id}`);
    return boardDetail.lists || [];
  }
  
  async createList(listData) {
    return this.request('/boards/lists', {
      method: 'POST',
      body: JSON.stringify(listData),
    });
  }
  
  async updateList(listId, listData) {
    return this.request(`/boards/lists/${listId}`, {
      method: 'PUT',
      body: JSON.stringify(listData),
    });
  }
  
  async deleteList(listId) {
    return this.request(`/boards/lists/${listId}`, {
      method: 'DELETE',
    });
  }
  
  async moveList(listId, newPosition) {
    return this.request(`/boards/lists/${listId}/position`, {
      method: 'PUT',
      body: JSON.stringify({ position: newPosition }),
    });
  }
  
  // Card API
  async getCards(listId) {
    return this.request(`/cards/list/${listId}`);
  }
  
  async createCard(cardData) {
    return this.request('/cards/', {
      method: 'POST',
      body: JSON.stringify(cardData),
    });
  }
  
  async updateCard(cardId, cardData) {
    return this.request(`/cards/${cardId}`, {
      method: 'PUT',
      body: JSON.stringify(cardData),
    });
  }
  
  async deleteCard(cardId) {
    return this.request(`/cards/${cardId}`, {
      method: 'DELETE',
    });
  }
  
  async moveCard(cardId, moveData) {
    return this.request(`/cards/${cardId}/move`, {
      method: 'PUT',
      body: JSON.stringify(moveData),
    });
  }
  
  // User API
  async getUsers() {
    return this.request('/users/');
  }
  
  async getUser(userId) {
    return this.request(`/users/${userId}`);
  }
  
  // Project Members API
  async addProjectMember(projectId, memberData) {
    return this.request(`/projects/${projectId}/members`, {
      method: 'POST',
      body: JSON.stringify(memberData),
    });
  }
  
  async removeProjectMember(projectId, userId) {
    return this.request(`/projects/${projectId}/members/${userId}`, {
      method: 'DELETE',
    });
  }
}

// Create singleton instance
export const apiService = new ApiService();