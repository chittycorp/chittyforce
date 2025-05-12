from notion_client import Client
from github import Github
import os
import json

# Notion setup
notion = Client(auth=os.getenv("NOTION_API_KEY"))

def create_task_in_notion(title, database_id):
    new_task = notion.pages.create(
        parent={"database_id": database_id},
        properties={
            "Name": {"title": [{"text": {"content": title}}]},
            "Status": {"select": {"name": "Not Started"}},
        },
    )
    return new_task

def update_task_status(task_id, status):
    notion.pages.update(
        **{
            "page_id": task_id,
            "properties": {
                "Status": {"select": {"name": status}},
            },
        }
    )

# GitHub setup
g = Github(os.getenv("GITHUB_API_KEY"))

def create_github_project_card(project_id, issue_id):
    project = g.get_repo('your-org/your-repo').get_projects(project_id)
    issue = g.get_repo('your-org/your-repo').get_issue(issue_id)
    
    project.create_card(content_id=issue.id, content_type='Issue')
