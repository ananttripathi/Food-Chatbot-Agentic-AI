# Contributing to FoodHub AI-Powered Chatbot (Agentic AI)

This repo hosts an **agentic chatbot** for food-delivery order queries: SQL agent over `customer_orders.db` → LLM-powered, guardrailed responses.

---

## Running Locally

1. **Clone and install**
   ```bash
   git clone https://github.com/ananttripathi/Food-Chatbot-Agentic-AI.git
   cd Food-Chatbot-Agentic-AI
   pip install -r requirements.txt
   ```
2. **API keys**  
   Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` (e.g. in `.env`). See [README → Installation](README.md#installation).
3. **Database**  
   Use `customer_orders.db` as the SQLite DB for the SQL agent. Schema: `order_id`, `cust_id`, `order_time`, `order_status`, `payment_status`, `item_in_order`, `preparing_eta`, `prepared_time`, `delivery_eta`, `delivery_time`.
4. **Implement & run**  
   Build per the [Evaluation Rubrics](README.md#evaluation-rubrics): LLM setup → SQL agent → Order Query Tool + Answer Tool → Chat agent → interactive loop. Use LangChain with OpenAI or Anthropic. Colab: set runtime to **T4 GPU**.

---

## Project Layout

- `README.md` — Overview, rubrics, data, setup, usage.
- `customer_orders.db` — Order database for the SQL agent.
- `requirements.txt` — Python deps (LangChain, OpenAI, etc.).

Add notebooks or `src/` as you implement the chatbot.

---

## Feedback

Open a [GitHub Issue](https://github.com/ananttripathi/Food-Chatbot-Agentic-AI/issues) for questions or suggestions.
