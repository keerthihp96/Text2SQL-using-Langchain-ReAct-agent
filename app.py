# app.py

import streamlit as st
from dotenv import load_dotenv
from database import test_connection
from agent import build_agent, run_agent, create_memory

load_dotenv()

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Text2SQL Agent",
    page_icon="🤖",
    layout="wide"      # wide layout — agent thoughts need space
)

st.title("🤖 Text2SQL Agentic AI")
st.caption("ReAct Agent powered by Groq LLaMA 3.3 + LangChain + Snowflake")


# ── Session State ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "memory" not in st.session_state:
    st.session_state.memory = create_memory()

if "agent" not in st.session_state:
    with st.spinner("🔧 Building ReAct Agent..."):
        st.session_state.agent = build_agent()
    st.success("✅ Agent ready!")


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Agent Settings")

    # Connection test
    if st.button("🔌 Test Snowflake Connection"):
        with st.spinner("Connecting..."):
            success, message = test_connection()
        if success:
            st.success(f"✅ {message}")
        else:
            st.error(f"❌ {message}")

    st.divider()

    # Display toggles
    show_thoughts = st.toggle(
        "🧠 Show Agent Thinking", value=True
    )
    show_tokens   = st.toggle(
        "📊 Show Token Usage",   value=True
    )

    st.divider()

    # Clear everything
    if st.button("🗑️ Clear Chat + Memory"):
        st.session_state.messages = []
        st.session_state.memory   = create_memory()
        st.rerun()

    st.divider()

    # Example questions
    st.markdown("**💡 Try these questions:**")
    examples = [
        "Who are the top 3 highest paid employees?",
        "Which department has the highest total salary?",
        "List all active projects and their assigned employees",
        "Who manages the Engineering department?",
        "How many employees are in each location?",
        "Which employees work on more than one project?",
    ]
    for q in examples:
        if st.button(q, use_container_width=True):
            st.session_state.pending_question = q
            st.rerun()

    st.divider()
    st.markdown("**🛠️ Agent Tools:**")
    tools_list = [
        "🔍 get_schema",
        "✍️ generate_sql",
        "✅ validate_sql",
        "⚡ execute_sql",
        "🚀 optimize_sql",
        "🔧 fix_sql_error",
        "💬 explain_results"
    ]
    for t in tools_list:
        st.markdown(f"- {t}")


# ── Helper: Render Agent Thinking Steps ──────────────────────────────────────
def render_agent_steps(steps: list):
    """Renders the agent's thinking process in a nice UI."""

    if not steps:
        return

    st.markdown("### 🧠 Agent Thinking Process")

    for i, step in enumerate(steps):

        if step["type"] == "thought":
            # Agent decided to use a tool
            with st.expander(
                f"🔄 Step {i+1}: Using **{step['tool']}**",
                expanded=False
            ):
                # Show agent's reasoning
                if step.get("log"):
                    thought_lines = [
                        line for line in step["log"].split("\n")
                        if line.strip().startswith("Thought:")
                    ]
                    if thought_lines:
                        st.markdown("**💭 Thought:**")
                        st.info(
                            thought_lines[0].replace("Thought:", "").strip()
                        )

                # Show tool input
                st.markdown("**📥 Tool Input:**")
                st.code(str(step["input"]), language="text")

        elif step["type"] == "observation":
            # Tool returned a result
            with st.expander(
                f"👁️ Step {i+1}: Observation",
                expanded=False
            ):
                st.markdown("**📤 Tool Output:**")
                output = step["output"]

                # Render SQL nicely
                if any(kw in output.upper() for kw in
                       ["SELECT", "FROM", "WHERE", "JOIN"]):
                    st.code(output, language="sql")
                else:
                    st.text(output)

        elif step["type"] == "final":
            # Agent reached final answer
            st.success(f"✅ **Final Answer reached after {i} steps**")


# ── Helper: Render Token Usage ────────────────────────────────────────────────
def render_token_usage(tokens: dict):
    col1, col2, col3 = st.columns(3)
    col1.metric("Prompt Tokens",     tokens.get("prompt", 0))
    col2.metric("Completion Tokens", tokens.get("completion", 0))
    col3.metric("Total Tokens",      tokens.get("total", 0))


# ── Render Past Messages ──────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Show agent steps for past assistant messages
        if (msg["role"] == "assistant"
                and show_thoughts
                and msg.get("steps")):
            render_agent_steps(msg["steps"])

        # Show token usage
        if (msg["role"] == "assistant"
                and show_tokens
                and msg.get("tokens")):
            render_token_usage(msg["tokens"])


# ── Handle Pending Question (from sidebar buttons) ────────────────────────────
user_input = st.session_state.pop("pending_question", None)
typed      = st.chat_input("Ask anything about your data...")
if typed:
    user_input = typed


# ── Main Agent Pipeline ───────────────────────────────────────────────────────
if user_input:

    # Show user message
    with st.chat_message("user"):
        st.markdown(user_input)

    st.session_state.messages.append({
        "role":    "user",
        "content": user_input
    })

    # Run agent
    with st.chat_message("assistant"):
        with st.spinner("🤖 Agent is thinking..."):
            result = run_agent(
                question=user_input,
                agent_executor=st.session_state.agent,
                memory=st.session_state.memory
            )

        # Show final answer
        st.markdown(result["answer"])

        # Show agent thinking steps
        if show_thoughts and result.get("steps"):
            render_agent_steps(result["steps"])

        # Show token usage
        if show_tokens and result.get("tokens"):
            st.markdown("**📊 Token Usage:**")
            render_token_usage(result["tokens"])

        # Show error if any
        if not result["success"]:
            st.error(f"⚠️ {result['error']}")

    # Save to display history
    st.session_state.messages.append({
        "role":    "assistant",
        "content": result["answer"],
        "steps":   result.get("steps", []),
        "tokens":  result.get("tokens", {})
    })
