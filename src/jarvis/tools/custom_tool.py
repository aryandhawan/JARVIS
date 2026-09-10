from crewai.tools import BaseTool,tool
from typing import Type
from pydantic import BaseModel, Field
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
import base64


@tool("Github read tool")
def github_read_tool():
    """this tool is used to read files from a Github repository."""
    pass

# @tool("get SHA token")
def git_sha_token(owner,repo,branch):
    """
    Get the SHA token for a specific file in a Github repository.

    Args:
        owner (str): The owner of the repository.
        repo (str): The name of the repository.
        branch (str): The branch name.


    Returns:
        str: The SHA token of the specified file.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {os.getenv('GITHUB_API_KEY')}"
    }
    
    response = httpx.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        SHA = data.get("object", {}).get("sha")
    else:
        raise Exception(f"Failed to get SHA token: {response.status_code} - {response.text}")


@tool("Github read tool")
def github_read_tool(owner: str, repo: str, path: str, branch: str):
    """This tool is used to read files from a GitHub repository."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {os.getenv('GITHUB_API_KEY')}"
    }

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"

    response = httpx.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()
    file_content = base64.b64decode(data["content"]).decode("utf-8")
    return file_content


@tool("create a git branch")
def create_git_branch(owner: str, repo: str, new_branch: str, base_branch: str):
    """This tool is used to create a new branch in a GitHub repository."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {os.getenv('GITHUB_API_KEY')}"
    }

    # Get the SHA of the base branch
    base_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{base_branch}"
    base_response = httpx.get(base_url, headers=headers)
    base_response.raise_for_status()
    base_sha = base_response.json().get("object", {}).get("sha")

    # Create the new branch
    create_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
    payload = {
        "ref": f"refs/heads/{new_branch}",
        "sha": base_sha
    }
    try:
        create_response = httpx.post(create_url, json=payload, headers=headers)
    except Exception as e:
        raise Exception(f"Error creating new branch: {e}")

    return f"Branch '{new_branch}' created successfully from '{base_branch}'."

@tool("Github write tool")
def github_write_tool(owner: str, repo: str, path: str, branch: str,content: str, commit_message: str):
    """This tool is used to write files to a GitHub repository."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {os.getenv('GITHUB_API_KEY')}"
    }
        # Get the SHA of the existing file (if it exists)
    get_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    get_response = httpx.get(get_url, headers=headers)
    if get_response.status_code == 200:
        sha = get_response.json().get("sha")


    url=f"PUT https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"

    payload = {"message": commit_message,
    "content": content,
    "branch": branch,
    "sha": sha}

    response = httpx.put(url, json=payload, headers=headers)

    return "File updated successfully."



if __name__ == "__main__":
    # Example usage
    owner = "aryandhawan"
    repo = "Lucid"
    path = "folder.py"
    branch = "main"
    new_branch = "feature-branch"
    base_branch = "main"
    try:
        print(create_git_branch(owner="aryandhawan", repo="Lucid", new_branch="feature-branch", base_branch="main"))

    except Exception as e:
        raise Exception(f"Error creating a new branch{e}")