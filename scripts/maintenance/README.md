# 维护脚本说明

本目录包含用于数据库维护、任务管理和问题排查的工具脚本。

## 📋 脚本列表

### 数据清理

#### `clear_all_data.py`
**功能**: 清空所有数据库数据和本地文件
- 删除所有 Repository、AnalysisTask、FileAnalysis、TaskReadme 记录
- 删除本地仓库目录 (data/repos/)
- 清空分析结果 (data/results/)
- 清空向量存储 (data/vectorstores/)

**使用场景**: 
- 重新开始全新的分析
- 清理测试数据
- 解决数据不一致问题

**运行方式**:
```bash
cd /path/to/codereader_workspace
python3 clear_all_data.py
```

#### `clean_duplicate_files.py`
**功能**: 清理数据库中的重复文件分析记录
- 检测同一任务中的重复文件记录
- 保留最新的记录，删除旧的重复记录
- 显示清理前后的统计信息

**使用场景**:
- 发现文件分析记录异常增多
- 同一文件被重复分析多次

**运行方式**:
```bash
cd /path/to/codereader_workspace
python3 clean_duplicate_files.py
```

---

### 任务管理

#### `check_all_tasks.py`
**功能**: 检查所有分析任务的状态
- 显示所有任务的基本信息
- 统计每个任务的文件分析数量
- 显示任务状态和进度

**运行方式**:
```bash
cd /path/to/codereader_workspace
python3 check_all_tasks.py
```

#### `check_task_status.py`
**功能**: 检查特定任务的详细状态
- 查看任务的所有字段信息
- 检查关联的文件分析记录

**运行方式**:
```bash
cd /path/to/codereader_workspace
python3 check_task_status.py
```

#### `check_task_41_files.py`
**功能**: 检查任务 41 的文件分析详情
- 专门用于调试任务 41 的问题
- 显示文件分析状态分布

**运行方式**:
```bash
cd /path/to/codereader_workspace
python3 check_task_41_files.py
```

#### `trigger_task_41.py`
**功能**: 手动触发任务 41 的执行
- 用于重新启动卡住的任务
- 强制执行特定任务

**运行方式**:
```bash
cd /path/to/codereader_workspace
python3 trigger_task_41.py
```

---

### 问题修复

#### `fix_stuck_tasks.py`
**功能**: 修复卡住的 Celery 任务
- 将状态为 "running" 但实际已停止的任务标记为 "completed"
- 清理僵尸任务

**使用场景**:
- Celery Worker 异常退出后任务状态未更新
- 任务显示 "running" 但实际没有在执行

**运行方式**:
```bash
cd /path/to/codereader_workspace
python3 fix_stuck_tasks.py
```

#### `fix_fastmcp_name.py`
**功能**: 修复 fastmcp 仓库的显示名称
- 更新 Repository 表中的 full_name
- 更新 README 文档标题

**使用场景**:
- 仓库名称显示为哈希值而不是实际名称
- 文档标题需要更新

**运行方式**:
```bash
cd /path/to/codereader_workspace
python3 fix_fastmcp_name.py
```

---

### 测试工具

#### `test_env_vars.py`
**功能**: 测试环境变量是否正确加载
- 检查所有必需的环境变量
- 验证 OpenAI API 配置
- 验证数据库配置

**使用场景**:
- 排查环境变量加载问题
- 验证配置是否正确

**运行方式**:
```bash
cd /path/to/codereader_workspace
python3 test_env_vars.py
```

---

## ⚠️ 注意事项

1. **数据备份**: 运行清理脚本前请确保已备份重要数据
2. **环境要求**: 所有脚本需要在正确配置 `.env` 文件后运行
3. **数据库连接**: 确保 MySQL 数据库正在运行
4. **权限问题**: 某些脚本可能需要文件系统写权限

---

## 🔧 常见问题

### Q: 脚本运行时提示找不到模块？
A: 确保在正确的目录下运行，并且已安装所有依赖：
```bash
cd Code-reader/backend
source .venv/bin/activate
pip install -r requirements.txt
```

### Q: 数据库连接失败？
A: 检查 `backend/.env` 文件中的数据库配置是否正确

### Q: 清理数据后无法恢复？
A: 这些脚本会永久删除数据，请在运行前确认

---

## 📝 维护日志

- 2025-11-30: 创建维护脚本目录，整理所有工具脚本

