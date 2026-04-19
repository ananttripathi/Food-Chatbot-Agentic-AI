import os
import re
import gradio as gr
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_core.messages import HumanMessage, SystemMessage

# --- LLM Setup ---
llm = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0,
    groq_api_key=os.environ.get("GROQ_API_KEY"),
)

# --- Database ---
db = SQLDatabase.from_uri("sqlite:///customer_orders.db")
sql_agent = create_sql_agent(
    llm=llm,
    db=db,
    verbose=False,
    handle_parsing_errors=True,
    max_iterations=3,
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


# --- Chatbot Function ---
def respond(message, history):
    is_safe, reason = check_guardrails(message)
    if not is_safe:
        return ESCALATION_RESPONSE if reason == "escalate" else BLOCKED_RESPONSE

    try:
        # Step 1: SQL agent fetches raw order data
        sql_result = sql_agent.invoke({"input": message})
        raw_data = sql_result.get("output", "")

        # Step 2: LLM formats it into a friendly response
        messages = [
            SystemMessage(content=(
                "You are a polite FoodHub customer service assistant. "
                "Convert the following raw order data into a friendly, clear, and "
                "professional customer response. Be concise and empathetic."
            )),
            HumanMessage(content=f"Customer question: {message}\nRaw data: {raw_data}"),
        ]
        return llm.invoke(messages).content

    except Exception as e:
        return f"DEBUG ERROR: {type(e).__name__}: {e}"


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
)


if __name__ == "__main__":
    demo.launch()
