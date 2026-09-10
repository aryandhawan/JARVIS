from crewai.tools import BaseTool,tool
from typing import Type
from pydantic import BaseModel, Field
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
import base64


@tool("get SHA token")
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
    """Read the current content of a file from a GitHub repository.
    
        Use this before proposing any change to an existing file — you must
        see the real, current content rather than assuming what it contains.
        Also use this to inspect config files, dependency lists, or any file
        you need to understand before deciding what to change.
    
        path is relative to the repo root, e.g. 'requirements.txt' or
        'src/main.py' — not a full URL or absolute filesystem path.
    
        branch is which version of the file to read — use the project's
        default branch (e.g. 'main') unless you are specifically checking
        content on a branch you already created.
    
        Returns the file's raw text content. If the file does not exist,
        this will raise an error — check with a file-listing tool first if
        you are unsure a file exists."""
    
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
    """Create a new branch in a GitHub repository, branched off an
    existing branch.

    Use this ONCE, at the start of making a change — you must always
    work on a dedicated branch, never commit directly to the base branch
    (e.g. 'main'). Create exactly one branch per change you are making;
    do not create a new branch for every file if a change touches
    multiple files.

    new_branch should be a clear, descriptive name indicating what the
    change does, e.g. 'jarvis/fix-retry-timeout' — not a generic name
    like 'update' or 'fix'.

    base_branch is almost always the project's default branch (e.g.
    'main') — the branch this new one is created from.

    After calling this, use the write tool to commit your actual changes
    to new_branch — do not attempt to write files before this branch
    exists."""

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
    """Write or update a file's content in a GitHub repository, creating
    a commit on the specified branch.

    ALWAYS pass the branch you created with the branch-creation tool —
    never write to the project's default branch (e.g. 'main') directly.

    If the file already exists, this correctly updates it in place based
    on its current content — you do not need to fetch or pass a SHA
    yourself, that is handled internally. If the file does not exist,
    this creates it.

    content must be the complete final content of the file, not a diff
    or partial edit — you are replacing the file's entire content with
    what you pass here.

    commit_message should clearly and specifically describe what changed
    and why, e.g. 'Fix retry timeout not applying on rate limit errors'
    — not a vague message like 'update file'.

    Call this once per file you are changing. You are limited to
    changing a maximum of 2 files for any single request — do not write
    to a third file."""

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {os.getenv('GITHUB_API_KEY')}"
    }
        # Get the SHA of the existing file (if it exists)
    get_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    get_response = httpx.get(get_url, headers=headers)
    sha=None
    if get_response.status_code == 200:
        sha = get_response.json().get("sha")


    url=f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"

    encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    payload = {"message": commit_message,
    "content": encoded_content,
    "branch": branch,
    "sha": sha}

    response = httpx.put(url, json=payload, headers=headers)

    return "File updated successfully."

@tool("create pull requests")
def create_pull_request(owner: str,repo: str,PR_title: str,description: str,head: str,base: str):
    """Open a pull request proposing your committed changes for human review.

    Call this EXACTLY ONCE, as the very last step, after all files for
    this change have already been written and committed to the branch
    via the write tool. Never call this before your changes exist on the
    branch — there must be a real diff for GitHub to show.

    PR_title should be short and specific, describing what changed.

    description should be a clear markdown summary: what changed, why,
    and what files were touched — this is what the human reviewing the
    PR will read to decide whether to merge it. This is your final
    report on the work you did.

    head is the branch you created and committed your changes to.
    base is the project's default branch (e.g. 'main') — where the
    change would merge into if approved.

    Opening this PR does NOT merge anything. The human must review and
    merge it manually. Your task is complete once this PR is opened —
    you do not take any further action after this."""

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {os.getenv('GITHUB_API_KEY')}"
        }

    payload={
        "title": PR_title,
        "body": description,
        "head": head,
        "base": base,
    }
    url=f"https://api.github.com/repos/{owner}/{repo}/pulls"

    response=httpx.post(url,headers=headers,json=payload)
    response.raise_for_status()

    pr_data = response.json()
    return pr_data.get("html_url")

if __name__ == "__main__":

    try:
        print(create_git_branch("aryandhawan", "Lucid", "test_branch", "main"))
        print(github_write_tool("aryandhawan", "Lucid", "test_file.txt", "test_branch", "This is a test file.", "Add test file"))
        print(create_pull_request("aryandhawan","Lucid","Test PR from JARVIS","does this work?","test_branch","main"))

    except Exception as e:
        raise Exception(f"Error creating a new branch{e}")