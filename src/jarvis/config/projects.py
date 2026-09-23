from pathlib import Path
import json

PROJECTS_FILE = Path(__file__).parent / "projects.json"
try:
    with open(PROJECTS_FILE, "r") as f:
        projects = json.load(f)
except FileNotFoundError:
    projects = {}

def add_project(project_name, repo_full_name, default_branch):
    """
    Add a new project to the projects dictionary.
    """
    projects[project_name] = {
        "repo_full_name": repo_full_name,
        "default_branch": default_branch
    }

    with open(PROJECTS_FILE, "w") as f:
        json.dump(projects, f, indent=4)

def get_project(project_name):
    """
    Get the project details for a given project name.
    """
    return projects.get(project_name, None)

def list_projects():
    """
    List all projects.
    """
    return list(projects.keys())

if __name__ == "__main__":
    # Example usage
    add_project("my_project", "username/my_project_repo", "main")
    print(get_project("my_project"))

