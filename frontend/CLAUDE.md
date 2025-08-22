# CLAUDE.md

此文件为Claude Code (claude.ai/code) 在处理此仓库代码时提供指导。

## 项目概述

这是一个名为"Taskly"的Vue.js任务管理应用程序，具有看板风格的界面。它是一个单页应用程序，使用Vue 3的组合式API、Pinia进行状态管理，以及Vue Router进行导航。该应用程序具有实时协作功能、多看板支持和中文语言界面。

## 开发命令

- `npm run dev` - 使用Vite启动开发服务器
- `npm run build` - 构建生产环境应用程序
- `npm run preview` - 预览生产构建

## 架构

### 核心框架栈
- **Vue 3** 使用组合式API和 `<script setup>` 语法
- **Pinia** 用于状态管理（替代Vuex，尽管也安装了Vuex）
- **Vue Router 4** 用于客户端路由，使用哈希历史模式
- **Vite** 作为构建工具和开发服务器
- **Bootstrap 5** 用于UI组件和样式
- **TailwindCSS** 通过CDN提供实用类
- **Font Awesome** 用于图标
- **Vue Toastification** 用于提示通知
- **Vue Draggable** 用于拖拽功能

### 应用程序结构
- **App.vue** - 主布局，包含侧边栏导航和路由视图
- **Views** - 页面级组件（首页、看板、仪表板、设置）
- **Components** - 可重用的UI组件（KanbanCard、KanbanList）
- **Stores** - Pinia状态管理存储
- **Router** - 基于哈希的路由，支持懒加载视图

### 主要功能
- **看板** - 使用Vue Draggable实现拖拽式任务管理，包含列表和卡片
- **实时协作** - WebSocket集成（目前为模拟，设计用于后端实现）
- **多看板支持** - 创建和管理多个项目看板
- **仪表板** - 使用Chart.js的分析和报告视图
- **中文界面** - 所有界面文本均为中文
- **导出功能** - 看板数据的JSON导出
- **用户管理** - 基本的用户配置文件和设置界面

### 状态管理
`boardStore` 管理：
- 看板数据结构（看板 → 列表 → 卡片层次结构）
- WebSocket连接状态和指数退避重连逻辑
- 离线支持，包含待处理更改队列
- 看板、列表和卡片的CRUD操作
- 客户端间实时同步（模拟）
- 连接状态监控

### 数据结构
```
Board {
  id: string,
  name: string,
  lists: List[]
}

List {
  id: string,
  name: string,
  cards: Card[]
}

Card {
  id: string,
  title: string,
  description: string,
  dueDate: string,
  labels: string[],
  assignedUsers: Array<{name: string}>
}
```

### 组件架构
- **KanbanList** - 处理列表级操作、卡片创建/编辑模态框、拖拽功能
- **KanbanCard** - 显示卡片信息、处理卡片操作、到期日期计算
- **BoardView** - 主看板界面，包含列表管理和看板操作
- **DashboardView** - 集成Chart.js的分析和报告
- **HomeView** - 功能亮点的着陆页
- **SettingsView** - 用户配置文件和应用程序设置

### 构建配置
- Vite配置，包含Vue插件和路径别名（`@` → `src`）
- 输出目录：`public/`
- 资源目录：`public/assets/`
- 基于哈希的路由，兼容部署

### 样式
- 在App.vue中通过CDN使用TailwindCSS实用类
- Bootstrap 5用于组件
- 自定义CSS变量用于主题
- Font Awesome图标用于UI元素
- Animate.css用于动画

### WebSocket集成
- boardStore中的模拟WebSocket连接（设计用于真实后端）
- 指数退避的自动重连逻辑
- 支持离线模式，包含更改队列
- 看板更改的实时更新
- UI中的连接状态指示器

### 拖拽功能
- Vue Draggable库用于看板功能
- 支持列表内和跨列表的卡片移动
- 使用ghost和chosen类提供视觉反馈
- 状态管理的乐观更新

## 重要说明

- 应用程序在整个界面中使用中文
- WebSocket功能目前为模拟，设计用于与后端服务器配合工作
- 构建输出到`public/`目录，该目录既用作静态资源托管，也是构建后的应用程序
- 所有状态管理都使用Pinia和组合式API
- 该应用程序设计用于协作任务管理，具有实时更新功能
- 包含Chart.js用于仪表板分析和报告
- 具有完整的用户偏好设置界面
- 支持看板数据的JSON导出，用于备份或迁移