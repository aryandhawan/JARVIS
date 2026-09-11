from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from pydantic import BaseModel,Field
from jarvis.tools.custom_tool import *
from jarvis.tools.docker_tool import *

class JudgementDecision(BaseModel):
    change_needed: bool
    reasoning: str
    files: list[str] = Field(default_factory=list, max_length=2)
    instruction: str = ""

@CrewBase
class Jarvis():
    """Jarvis crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def judgement_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['Judgement_agent' ], # type: ignore[index]
            tools=[github_read_tool],
            verbose=True,
        )

    @agent
    def maintainence_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['maintainence_agent'], # type: ignore[index]
            verbose=True,
            mcps=["https://mcp.context7.com/mcp"],
            tools=[git_sha_token,github_write_tool,create_git_branch,create_pull_request,restart_container,get_container_logs,check_container_status]
        )

    @task
    def investigate_and_judge_task(self) -> Task:
        return Task(
            config=self.tasks_config['investigate_and_judge'], # type: ignore[index]
            output_pydantic=JudgementDecision
        )

    @task
    def execute_change_task(self) -> Task:
        return Task(
            config=self.tasks_config['execute_change'], # type: ignore[index]
            output_file='report.md'
        )

    @task
    def routine_check_task(self) -> Task:
        return Task(
            config=self.tasks_config['routine_check'],
        )


    @crew
    def crew(self) -> Crew:
        """Creates the Jarvis crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            tracing=True
        )

    
def run_routine_check(repo_list: list[str]):
    jarvis = Jarvis()
    tasks = [jarvis.routine_check_task()]

    routine_crew = Crew(
        agents=[jarvis.judgement_agent()],
        tasks=tasks,
        process=Process.sequential,
    )
    result = routine_crew.kickoff(inputs={"repo_list": ", ".join(repo_list)})
    return result.raw