from crewai.tools import tool
from pathlib import Path
import subprocess
import docker

client=docker.from_env()

@tool("Check container status")
def check_container_status(container_name: str)->str:
    """Check whether a Docker container is currently running, and its
    basic status. Use this first when investigating whether a project's
    local container is healthy, before pulling logs or restarting."""
    client = docker.from_env()
    try:
        container = client.containers.get(container_name)
        return f"{container_name}: status={container.status}"
    except docker.errors.NotFound:
        return {"status": "not found"}
    except Exception as e:
        return {"error": str(e)}

@tool("get container logs")
def get_container_logs(container_name: str,tail: int=100)-> str:
    """Get the most recent log lines from a container, to diagnose why
    it might be unhealthy or erroring. Use this after checking status,
    if the container is not running as expected."""
    try:
        container=client.containers.get(container_name)
        logs=container.logs(tail=tail)
        return logs.decode("utf-8",errors="replace")
    except docker.errors.NotFound:
        return f"Error: no container named {container_name} found"
    except docker.errors.APIError as e:
        return f"Error: API Error - {e}"

@tool("Restart Container")
def restart_container(container_name: str)->str:
    """Restart a Docker container. Only use this when logs or status
    genuinely indicate the container is faulty (crashed, stuck,
    unresponsive) — this causes a brief outage for whatever it's serving.
    Do not use this speculatively."""
    try:
        container=client.containers.get(container_name)
        container.restart(timeout=10)
        return f"Container {container_name} restarted successfully."
    except docker.errors.NotFound:
        return f"ERROR: no container named '{container_name}' found."
    except docker.errors.APIError as e:
        return f"ERROR: Docker API error — {e}"

if __name__=="__main__":
    print(restart_container("jarvis-test-container"))
    