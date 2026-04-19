import os
import re
import gradio as gr
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain.agents import AgentType, initialize_agent, Tool
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, SystemMessage

# --- LLM Setup ---
llm = ChatGroq(
    model="llama3-8b-8192",
    temperature=0,
    groq_api_key=os.environ.get("GROQ_API_KEY"),
)

# --- Database ---
db = SQLDatabase.from_uri("sqlite:///customer_orders.db")
sql_agent = create_sql_agent(
    llm=llm,
    db=db,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=False,
    handle_parsing_errors=True,
)

# --- Guardrails ---
BLOCKED_PATTERNS = [
    r"(drop|delete|truncate|alter|insert|update)\s+",
    r"(all\s+orders|every\s+order|dump|export\s+all)",
    r"(hacker|hack|exploit|bypass|admin|root|password)",
    r"(select\s+\*|show\s+all)",
]

ESCALATION_TRIGGERS = [
    "multiple times", "no resolution", "immediate response",
    "unacceptable", "lawsuit", "complaint", "manager", "supervisor"
]

BLOCKED_RESPONSE = (
    "I'm sorry, I'm unable to process that request. "
    "Please ask about your specific order details."
)

ESCALATION_RESPONSE = (
    "I understand your frustration and sincerely apologize for the inconvenience. "
    "I'm escalating your case to a senior human agent who will prioritize your concern "
    "and reach out within 30 minutes. Your patience is greatly appreciated. 🙏"
)


def check_guardrails(text: str) -> tuple:
    lower = text.lower()
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, lower):
            return False, "blocked"
    for trigger in ESCALATION_TRIGGERS:
        if trigger in lower:
            return False, "escalate"
    return True, "safe"


# --- Tools ---
def order_query_tool(query: str) -> str:
    try:
        result = sql_agent.invoke({"input": query})
        return result["output"]
    except Exception as e:
        return f"Error fetching order data: {str(e)}"


def answer_tool(raw_data: str) -> str:
    messages = [
        SystemMessage(content=(
            "You are a polite FoodHub customer service assistant. "
            "Convert the following raw order data into a friendly, "
            "clear, and professional customer response. Be concise and empathetic."
        )),
        HumanMessage(content=f"Raw order data: {raw_data}")
    ]
    return llm.invoke(messages).content


tools = [
    Tool(name="OrderQueryTool", func=order_query_tool,
         description="Fetches order details from the database using natural language."),
    Tool(name="AnswerTool", func=answer_tool,
         description="Converts raw order data into a polite customer-friendly response."),
]

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

chat_agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=False,
    handle_parsing_errors=True,
)


# --- Chatbot Function ---
def respond(message, history):
    is_safe, reason = check_guardrails(message)

    if not is_safe:
        return ESCALATION_RESPONSE if reason == "escalate" else BLOCKED_RESPONSE

    try:
        result = chat_agent.invoke({"input": message})
        return result["output"]
    except Exception:
        return (
            "I apologize, I'm experiencing a technical issue. "
            "Please try again or contact support@foodhub.com."
        )


# --- Gradio UI ---
demo = gr.ChatInterface(
    fn=respond,
    title="🍔 FoodHub AI Customer Support",
    description=(
        "Ask about your order status, delivery time, payment details, or cancellations. "
        "Provide your **Order ID** (e.g. O12488) for order-specific queries.\n\n"
        "**Sample questions:**\n"
        "- Where is my order O12488?\n"
        "- What is the status of order O12486?\n"
        "- I want to cancel my order O12487"
    ),
    examples=[
        "Where is my order O12488?",
        "What is the payment status of order O12488?",
        "I want to cancel my order O12487",
        "What items are in order O12488?",
    ],
    theme=gr.themes.Soft(),
)

if __name__ == "__main__":
    demo.launch()
