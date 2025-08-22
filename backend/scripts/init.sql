-- 创建数据库和用户（如果不存在）
-- CREATE DATABASE SyncBoard;
-- CREATE USER root WITH PASSWORD '123456';
-- GRANT ALL PRIVILEGES ON DATABASE SyncBoard TO root;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO root;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO root;

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建索引（在数据导入后）
-- CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
-- CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
-- CREATE INDEX IF NOT EXISTS idx_boards_owner_id ON boards(owner_id);
-- CREATE INDEX IF NOT EXISTS idx_lists_board_id ON lists(board_id);
-- CREATE INDEX IF NOT EXISTS idx_cards_list_id ON cards(list_id);
-- CREATE INDEX IF NOT EXISTS idx_cards_assigned_user_id ON cards(assigned_user_id);
-- CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id);
-- CREATE INDEX IF NOT EXISTS idx_activity_logs_entity_type ON activity_logs(entity_type);
-- CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON activity_logs(created_at);

-- 创建全文搜索索引（可选）
-- CREATE INDEX IF NOT EXISTS idx_cards_title_search ON cards USING gin(to_tsvector('english', title));
-- CREATE INDEX IF NOT EXISTS idx_cards_description_search ON cards USING gin(to_tsvector('english', description));

-- 插入示例数据（可选）
-- INSERT INTO users (email, username, full_name, hashed_password, is_active) VALUES
-- ('admin@example.com', 'admin', 'Administrator', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeZeUfkZMBs9kYZP6', true),
-- ('user@example.com', 'user', 'Test User', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeZeUfkZMBs9kYZP6', true);

-- 插入示例看板数据（可选）
-- INSERT INTO boards (name, description, owner_id) VALUES
-- ('我的第一个项目', '这是一个示例项目', 1),
-- ('团队协作看板', '团队协作示例', 1);

-- 插入示例列表数据（可选）
-- INSERT INTO lists (name, position, board_id) VALUES
-- ('待办', 0, 1),
-- ('进行中', 1, 1),
-- ('已完成', 2, 1),
-- ('待办', 0, 2),
-- ('进行中', 1, 2),
-- ('已完成', 2, 2);

-- 插入示例卡片数据（可选）
-- INSERT INTO cards (title, description, position, list_id, assigned_user_id) VALUES
-- ('调研竞争对手', '分析前3名竞争对手', 0, 1, 2),
-- ('创建线框图', '设计初始UI概念', 1, 1, 2),
-- ('搭建开发环境', '安装所有必要的工具和依赖', 0, 2, 2),
-- ('项目启动会议', '团队首次会议讨论项目目标', 0, 3, 1);