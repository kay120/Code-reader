-- 添加current_file字段到analysis_tasks表
-- 用于记录当前正在处理的文件路径

USE code_reader;

-- 添加current_file字段
ALTER TABLE analysis_tasks 
ADD COLUMN current_file VARCHAR(1024) NULL COMMENT '当前正在处理的文件路径' 
AFTER status;

-- 验证字段是否添加成功
SELECT 
    COLUMN_NAME, 
    COLUMN_TYPE, 
    IS_NULLABLE, 
    COLUMN_COMMENT 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'code_reader' 
  AND TABLE_NAME = 'analysis_tasks' 
  AND COLUMN_NAME = 'current_file';

