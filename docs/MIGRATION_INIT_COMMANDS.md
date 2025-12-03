# Ragflow 服务迁移 - 数据库初始化命令汇总

## 概述

以下命令用于初始化 Ragflow 多用户环境，确保系统正常运行。在新环境部署后执行一次即可。

## 前提条件

1. Ragflow 容器已启动
2. MySQL 容器已启动（容器名: `ragflow-mysql`）
3. `admin@qq.com` 用户已通过正常注册流程创建

## 初始化命令

### 步骤 1: 获取 admin 用户 ID

```bash
docker exec -it ragflow-mysql mysql -uroot -pinfini_rag_flow -e "USE rag_flow; SELECT id, email FROM user WHERE email = 'admin@qq.com';"
```

记录返回的 `id` 值（示例: `23e8a3eaa99211f0b8443a2439c59073`）

### 步骤 2: 创建 Tenant 记录

将 `<USER_ID>` 替换为步骤1获取的 ID：

```bash
docker exec -it ragflow-mysql mysql -uroot -pinfini_rag_flow -e "
USE rag_flow;
INSERT INTO tenant (id, name, llm_id, embd_id, asr_id, parser_ids, img2txt_id, rerank_id, credit, status, create_time, update_time)
VALUES ('<USER_ID>', 'Admin Kingdom', 'deepseek-chat', 'BAAI/bge-large-zh-v1.5', '', 'naive', '', 'BAAI/bge-reranker-v2-m3', 512, '1', UNIX_TIMESTAMP()*1000, UNIX_TIMESTAMP()*1000);
"
```

### 步骤 3: 创建 UserTenant 记录

```bash
docker exec -it ragflow-mysql mysql -uroot -pinfini_rag_flow -e "
USE rag_flow;
INSERT INTO user_tenant (id, user_id, tenant_id, role, invited_by, status, create_time, update_time)
VALUES (REPLACE(UUID(),'-',''), '<USER_ID>', '<USER_ID>', 'owner', '<USER_ID>', '1', UNIX_TIMESTAMP()*1000, UNIX_TIMESTAMP()*1000);
"
```

### 步骤 4: 创建 File 根目录

```bash
docker exec -it ragflow-mysql mysql -uroot -pinfini_rag_flow -e "
USE rag_flow;
SET @file_id = REPLACE(UUID(),'-','');
INSERT INTO file (id, parent_id, tenant_id, created_by, name, type, size, location, source_type, create_time, update_time)
VALUES (@file_id, @file_id, '<USER_ID>', '<USER_ID>', '/', 'folder', 0, '', '', UNIX_TIMESTAMP()*1000, UNIX_TIMESTAMP()*1000);
"
```

### 步骤 5: 配置 TenantLLM 模型

在 Ragflow 管理界面或通过 API 配置 LLM 模型（如 SILICONFLOW 的 deepseek 模型）

### 步骤 6: 更新 Tenant 的默认 LLM

```bash
docker exec -it ragflow-mysql mysql -uroot -pinfini_rag_flow -e "
USE rag_flow;
UPDATE tenant SET llm_id = 'deepseek-ai/DeepSeek-R1-Distill-Qwen-32B@SILICONFLOW' WHERE id = '<USER_ID>';
"
```

### 步骤 7: 更新 Dialog 的 LLM（如有）

```bash
docker exec -it ragflow-mysql mysql -uroot -pinfini_rag_flow -e "
USE rag_flow;
UPDATE dialog SET llm_id = 'deepseek-ai/DeepSeek-R1-Distill-Qwen-32B@SILICONFLOW' WHERE llm_id = 'deepseek-chat';
"
```

## 验证命令

```bash
# 检查 tenant 记录
docker exec -it ragflow-mysql mysql -uroot -pinfini_rag_flow -e "USE rag_flow; SELECT id, name, llm_id FROM tenant;"

# 检查 user_tenant 记录
docker exec -it ragflow-mysql mysql -uroot -pinfini_rag_flow -e "USE rag_flow; SELECT * FROM user_tenant;"

# 检查 tenant_llm 模型配置
docker exec -it ragflow-mysql mysql -uroot -pinfini_rag_flow -e "USE rag_flow; SELECT llm_name, llm_factory FROM tenant_llm WHERE model_type = 'chat' LIMIT 5;"
```

## 注意事项

1. `<USER_ID>` 需替换为实际的 admin 用户 ID（32位无横线的 UUID）
2. `llm_id` 应使用实际配置的模型名称（格式: `模型名@厂商名`）
3. 密码 `infini_rag_flow` 根据实际部署配置调整

## 一键初始化脚本

为方便使用，可以将以下脚本保存为 `init_ragflow_db.sh`：

```bash
#!/bin/bash

# Ragflow 数据库初始化脚本
# 使用方法: ./init_ragflow_db.sh

MYSQL_CONTAINER="ragflow-mysql"
MYSQL_USER="root"
MYSQL_PASSWORD="infini_rag_flow"
DATABASE="rag_flow"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Ragflow 数据库初始化 ===${NC}"

# 步骤1: 获取 admin 用户 ID
echo -e "\n${GREEN}步骤 1: 获取 admin 用户 ID${NC}"
USER_ID=$(docker exec -i $MYSQL_CONTAINER mysql -u$MYSQL_USER -p$MYSQL_PASSWORD -N -e "USE $DATABASE; SELECT id FROM user WHERE email = 'admin@qq.com';")

if [ -z "$USER_ID" ]; then
    echo -e "${RED}错误: 未找到 admin@qq.com 用户，请先通过注册流程创建该用户${NC}"
    exit 1
fi

echo "找到用户 ID: $USER_ID"

# 步骤2: 检查并创建 Tenant
echo -e "\n${GREEN}步骤 2: 创建 Tenant 记录${NC}"
TENANT_EXISTS=$(docker exec -i $MYSQL_CONTAINER mysql -u$MYSQL_USER -p$MYSQL_PASSWORD -N -e "USE $DATABASE; SELECT COUNT(*) FROM tenant WHERE id = '$USER_ID';")

if [ "$TENANT_EXISTS" -eq "0" ]; then
    docker exec -i $MYSQL_CONTAINER mysql -u$MYSQL_USER -p$MYSQL_PASSWORD -e "
    USE $DATABASE;
    INSERT INTO tenant (id, name, llm_id, embd_id, asr_id, parser_ids, img2txt_id, rerank_id, credit, status, create_time, update_time)
    VALUES ('$USER_ID', 'Admin Kingdom', 'deepseek-chat', 'BAAI/bge-large-zh-v1.5', '', 'naive', '', 'BAAI/bge-reranker-v2-m3', 512, '1', UNIX_TIMESTAMP()*1000, UNIX_TIMESTAMP()*1000);
    "
    echo "Tenant 记录已创建"
else
    echo "Tenant 记录已存在，跳过"
fi

# 步骤3: 检查并创建 UserTenant
echo -e "\n${GREEN}步骤 3: 创建 UserTenant 记录${NC}"
USER_TENANT_EXISTS=$(docker exec -i $MYSQL_CONTAINER mysql -u$MYSQL_USER -p$MYSQL_PASSWORD -N -e "USE $DATABASE; SELECT COUNT(*) FROM user_tenant WHERE user_id = '$USER_ID' AND tenant_id = '$USER_ID';")

if [ "$USER_TENANT_EXISTS" -eq "0" ]; then
    docker exec -i $MYSQL_CONTAINER mysql -u$MYSQL_USER -p$MYSQL_PASSWORD -e "
    USE $DATABASE;
    INSERT INTO user_tenant (id, user_id, tenant_id, role, invited_by, status, create_time, update_time)
    VALUES (REPLACE(UUID(),'-',''), '$USER_ID', '$USER_ID', 'owner', '$USER_ID', '1', UNIX_TIMESTAMP()*1000, UNIX_TIMESTAMP()*1000);
    "
    echo "UserTenant 记录已创建"
else
    echo "UserTenant 记录已存在，跳过"
fi

# 步骤4: 检查并创建 File 根目录
echo -e "\n${GREEN}步骤 4: 创建 File 根目录${NC}"
FILE_EXISTS=$(docker exec -i $MYSQL_CONTAINER mysql -u$MYSQL_USER -p$MYSQL_PASSWORD -N -e "USE $DATABASE; SELECT COUNT(*) FROM file WHERE tenant_id = '$USER_ID' AND name = '/';")

if [ "$FILE_EXISTS" -eq "0" ]; then
    docker exec -i $MYSQL_CONTAINER mysql -u$MYSQL_USER -p$MYSQL_PASSWORD -e "
    USE $DATABASE;
    SET @file_id = REPLACE(UUID(),'-','');
    INSERT INTO file (id, parent_id, tenant_id, created_by, name, type, size, location, source_type, create_time, update_time)
    VALUES (@file_id, @file_id, '$USER_ID', '$USER_ID', '/', 'folder', 0, '', '', UNIX_TIMESTAMP()*1000, UNIX_TIMESTAMP()*1000);
    "
    echo "File 根目录已创建"
else
    echo "File 根目录已存在，跳过"
fi

echo -e "\n${YELLOW}=== 初始化完成 ===${NC}"
echo -e "${YELLOW}请在 Ragflow 管理界面配置 LLM 模型后，执行以下命令更新默认模型:${NC}"
echo ""
echo "docker exec -it $MYSQL_CONTAINER mysql -u$MYSQL_USER -p$MYSQL_PASSWORD -e \"USE $DATABASE; UPDATE tenant SET llm_id = '<MODEL_NAME>@<FACTORY>' WHERE id = '$USER_ID';\""
echo ""
echo -e "${GREEN}验证命令:${NC}"
echo "docker exec -it $MYSQL_CONTAINER mysql -u$MYSQL_USER -p$MYSQL_PASSWORD -e \"USE $DATABASE; SELECT id, name, llm_id FROM tenant;\""
```

