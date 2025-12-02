#!/usr/bin/env python3
"""
重新分析仓库的便捷脚本

使用方法:
    python scripts/reanalyze_repository.py <repository_id>
    
示例:
    python scripts/reanalyze_repository.py 3
"""

import sys
import requests
import json

def reanalyze_repository(repository_id: int, api_url: str = "http://localhost:8000"):
    """
    重新分析指定的仓库
    
    Args:
        repository_id: 仓库ID
        api_url: API 基础URL
    """
    url = f"{api_url}/api/analysis/repository/{repository_id}/reanalyze"
    
    print(f"🚀 正在重新分析仓库 {repository_id}...")
    
    try:
        response = requests.post(url)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("status") == "success":
            print(f"✅ 重新分析任务已创建！")
            print(f"   仓库ID: {result.get('repository_id')}")
            print(f"   仓库名称: {result.get('repository_name')}")
            print(f"   任务ID: {result.get('task_id')}")
            print(f"   Celery任务ID: {result.get('celery_task_id')}")
            print(f"\n💡 任务已提交到后台队列，请在前端查看进度")
            return result.get('task_id')
        else:
            print(f"❌ 重新分析失败: {result.get('message')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {str(e)}")
        return None

def list_repositories(api_url: str = "http://localhost:8000"):
    """列出所有仓库"""
    url = f"{api_url}/api/repositories"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        repos = response.json()
        
        if repos:
            print("📦 现有仓库列表:")
            for repo in repos:
                print(f"   ID: {repo.get('id')}, 名称: {repo.get('name')}")
        else:
            print("没有找到仓库")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python scripts/reanalyze_repository.py <repository_id>")
        print("\n或者查看所有仓库:")
        print("python scripts/reanalyze_repository.py --list")
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        list_repositories()
    else:
        try:
            repo_id = int(sys.argv[1])
            reanalyze_repository(repo_id)
        except ValueError:
            print("❌ 仓库ID必须是数字")
            sys.exit(1)

