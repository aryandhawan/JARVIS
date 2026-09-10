#!/usr/bin/env python
import sys
import warnings
from fastapi import FastAPI,Request
from pydantic import BaseModel,Field
from datetime import datetime
from openai import AsyncOpenAI
from jarvis.crew import Jarvis
import os
from dotenv import load_dotenv

load_dotenv()


class ChatRequest(BaseModel):
    conversation_id: str = Field(..., description="The unique identifier for the conversation.")
    user_message: str = Field(..., description="The message from the user to be processed by the AI model.")

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

app=FastAPI(title="Jarvis API", description="API for Jarvis Crew", version="1.0.0")


client=AsyncOpenAI(api_key=os.getenv("GOOGLE_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

JARVIS_CHAT_SYSTEM_PROMPT = """You are JARVIS, a personal AI assistant for a solo AI
engineer who runs multiple software projects. You are the conversational
layer — you talk through ideas, bugs, and possible changes with the
engineer before anything is actually investigated or executed.

You do NOT have access to the engineer's actual code, logs, or
repositories in this conversation. Do not claim to have read, checked,
or found anything in their code — you haven't. If they describe a bug or
ask about a specific issue, you can reason about it in general terms,
ask clarifying questions, and help them think it through, but you must
be explicit that real investigation only happens once they trigger it.

Your job in this conversation:
- Understand what the engineer wants to look into or change
- Ask clarifying questions if their request is vague ("optimize it" is
  not specific enough — ask what's actually prompting the request)
- Help them reason about whether something is worth investigating at all
- Never fabricate findings, code snippets, or specifics you don't have

When the engineer sends the exact phrase "fire up the arc", that means they are confirming they want
you to hand this conversation off for real investigation and action.
Do not treat any other phrasing — "yes", "do it", "sounds good" — as
this trigger, even if it seems like agreement. Only the exact trigger
phrase means proceed.

Keep your tone direct and collaborative — you are a thinking partner,
not a yes-man. If something the engineer suggests seems like a bad idea
or underspecified, say so plainly before they trigger execution, not
after."""

chat_history = {}

@app.post("/chat")
async def chat(request: ChatRequest):
    user_message = request.user_message


    previous_messages = chat_history.get(request.conversation_id, [])

    
    messages = [{"role": "system", "content": JARVIS_CHAT_SYSTEM_PROMPT}] \
        + previous_messages \
        + [{"role": "user", "content": user_message}]

    response = await client.chat.completions.create(
        model="gemini-3.8-flash",
        messages=messages,
    )
    reply_text = response.choices[0].message.content

    
    chat_history[request.conversation_id] = previous_messages + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": reply_text},
    ]

    if user_message.strip().lower() == "fire up the arc":
        try:
            result = run_with_trigger(inputs={
                "crewai_trigger_payload": chat_history[request.conversation_id]
            })
            return {"message": "JARVIS has engaged and executed the task.", "result": result}
        except Exception as e:
            return {"error": str(e)}

    return {"message": reply_text}

def run():
    """
    Run the crew.
    """
    inputs = {
        'topic': 'AI LLMs',
        'current_year': str(datetime.now().year)
    }

    try:
        Jarvis().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        Jarvis().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        Jarvis().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    try:
        Jarvis().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "topic": "",
        "current_year": ""
    }

    try:
        result = Jarvis().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
