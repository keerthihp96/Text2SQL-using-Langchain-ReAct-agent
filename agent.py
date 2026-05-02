# agent.py

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.globals import set_llm_cache
from langchain_core.caches import InMemoryCache
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from langchain_core.chat_history import InMemoryChatMessageHistory
from tools import all_tools

load_dotenv()

# ── Caching ───────────────────────────────────────────────────────────────────
set_llm_cache(InMemoryCache())


# ── Callback: Capture agent thoughts for Streamlit ───────────────────────────
class AgentCallbackHandler(BaseCallbackHandler):
    """
    Captures every agent thought, tool call, and result
    so Streamlit can display the thinking process live.
    """

    def __init__(self):
        self.steps = []      # stores all thinking steps
        self.tokens = {
            "prompt": 0,
            "completion": 0,
            "total": 0
        }

    def on_agent_action(self, action, **kwargs):
        """Fires when agent decides to use a tool."""
        self.steps.append({
            "type":  "thought",
            "tool":  action.tool,
            "input": action.tool_input,
            "log":   action.log
        })

    def on_tool_end(self, output, **kwargs):
        """Fires when a tool returns its result."""
        self.steps.append({
            "type":   "observation",
            "output": str(output)[:500]   # truncate for display
        })

    def on_llm_end(self, response, **kwargs):
        """Fires after every LLM call — tracks token usage."""
        usage = response.llm_output.get("token_usage", {})
        self.tokens["prompt"]     += usage.get("prompt_tokens", 0)
        self.tokens["completion"] += usage.get("completion_tokens", 0)
        self.tokens["total"]      += usage.get("total_tokens", 0)

    def on_agent_finish(self, finish, **kwargs):
        """Fires when agent reaches final answer."""
        self.steps.append({
            "type":   "final",
            "output": finish.return_values.get("output", "")
        })

    def reset(self):
        """Clear steps between questions."""
        self.steps  = []
        self.tokens = {"prompt": 0, "completion": 0, "total": 0}


# ── Global callback instance ──────────────────────────────────────────────────
agent_callback = AgentCallbackHandler()


# ── ReAct Prompt ──────────────────────────────────────────────────────────────
REACT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert Text-to-SQL AI Agent working with a Snowflake database.

You have access to these tools:
- get_schema: ALWAYS call this FIRST to understand the database structure
- generate_sql: Convert a question to SQL after checking schema
- validate_sql: ALWAYS validate SQL before executing
- execute_sql: Run the validated SQL on Snowflake
- optimize_sql: Optimize SQL for better performance (use when query is complex)
- fix_sql_error: Fix SQL if execution fails
- explain_results: ALWAYS use this LAST to give user a natural language answer

STRICT WORKFLOW — follow this exact order every time:
1. get_schema → call this ONCE only at the start, never again
2. generate_sql → Before returning, verify the SQL is valid Snowflake syntax.
3. optimize_sql → ONLY use for complex multi-join queries, skip for simple ones
4. execute_sql → run on Snowflake
5. fix_sql_error → only if step 4 fails, then retry step 4
6. explain_results → always give final natural language answer


Think carefully at each step. If a tool returns an error, 
use fix_sql_error and retry. Never give up after one failure.

{tools}

Use the following format STRICTLY:

Question: the input question you must answer
Thought: your reasoning about what to do next
Action: the tool name (must be one of [{tool_names}])
Action Input: the input to the tool
Observation: the result of the tool
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now know the final answer
Final Answer: the complete answer to the user's question
"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    ("assistant", "{agent_scratchpad}")
])


# ── Build Agent ───────────────────────────────────────────────────────────────
def build_agent():
    """Builds and returns the ReAct AgentExecutor."""

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=st.secrets["GROQ_API_KEY"],
        temperature=0,
        max_tokens=4096,     # agents need more tokens for reasoning
        max_retries=3,
        callbacks=[agent_callback]
    )

    # Create ReAct agent
    agent = create_react_agent(
        llm=llm,
        tools=all_tools,
        prompt=REACT_PROMPT
    )

    # Wrap in executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=all_tools,
        verbose=True,               # prints to terminal
        max_iterations=10,          # prevents infinite loops
        handle_parsing_errors=True, # recovers from format errors
        return_intermediate_steps=True,
        callbacks=[agent_callback]
    )

    return agent_executor


# ── Memory ────────────────────────────────────────────────────────────────────
def create_memory() -> InMemoryChatMessageHistory:
    return InMemoryChatMessageHistory()


# ── Run Agent ─────────────────────────────────────────────────────────────────
def run_agent(
    question: str,
    agent_executor: AgentExecutor,
    memory: InMemoryChatMessageHistory
) -> dict:
    """
    Runs the agent on a question.
    Returns answer + all intermediate steps for display.
    """

    # Reset callback steps for this question
    agent_callback.reset()

    # Build chat history for context
    chat_history = memory.messages[-6:]

    try:
        result = agent_executor.invoke({
            "input":        question,
            "chat_history": chat_history
        })

        answer = result.get("output", "No answer generated")

        # Save to memory
        memory.add_user_message(question)
        memory.add_ai_message(answer)

        return {
            "answer":  answer,
            "steps":   agent_callback.steps,
            "tokens":  agent_callback.tokens,
            "success": True,
            "error":   None
        }

    except Exception as e:
        return {
            "answer":  f"Agent encountered an error: {str(e)}",
            "steps":   agent_callback.steps,
            "tokens":  agent_callback.tokens,
            "success": False,
            "error":   str(e)
        }
