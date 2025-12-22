# Databricks notebook source
# MAGIC %md
# MAGIC # RAG Chatbot for Customer KWH Summary
# MAGIC Using LangGraph without Vector Search
# MAGIC
# MAGIC This notebook creates a RAG (Retrieval-Augmented Generation) chatbot that:
# MAGIC 1. Converts natural language questions to SQL queries
# MAGIC 2. Retrieves relevant data from `gold_daily_customer_kwh_summary` table
# MAGIC 3. Generates natural language responses using LLM
# MAGIC
# MAGIC **Table**: `na-dbxtraining.biju_gold.gold_daily_customer_kwh_summary`

# COMMAND ----------

# MAGIC %md
# MAGIC ![Description](/Workspace/Users/biju.thottathil@3cloudsolutions.com/training/databricksinternaldemo/mcpserver/ragchat.png)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Install Required Packages

# COMMAND ----------

# MAGIC %pip install langchain langchain-databricks langgraph gradio databricks-sdk databricks-langchain

# COMMAND ----------

# MAGIC %pip install --upgrade databricks-langchain langchain-community langchain databricks-sql-connector

# COMMAND ----------

dbutils.library.restartPython() 

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup and Configuration

# COMMAND ----------

try:
    from databricks_langchain import ChatDatabricks
except ImportError:
    # Fallback to old import
    from langchain_community.chat_models import ChatDatabricks
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
import operator
import os

# Configuration
CATALOG = "na-dbxtraining"
SCHEMA = "biju_gold"
TABLE = "gold_daily_customer_kwh_summary_ne"
FULL_TABLE = f"`{CATALOG}`.{SCHEMA}.{TABLE}"

# LLM Configuration - Update this based on your workspace
# Option 1: Use Foundation Model API (recommended)
# Available models: "databricks-meta-llama-3-70b-instruct", "databricks-mixtral-8x7b-instruct", etc.
# Option 2: Use your custom serving endpoint name
LLM_ENDPOINT = "databricks-meta-llama-3-1-8b-instruct"  # Change this to your available model

print(f"✅ Configuration loaded")
print(f"   Table: {FULL_TABLE}")
print(f"   LLM Endpoint: {LLM_ENDPOINT}")
print(f"\n💡 To find available models, check:")
print(f"   - Databricks Foundation Models: https://docs.databricks.com/en/machine-learning/foundation-models/index.html")
print(f"   - Or check your Serving endpoints in Databricks UI")


# COMMAND ----------

# MAGIC %md
# MAGIC ## Define State and Graph Structure

# COMMAND ----------

class ChatState(TypedDict):
    messages: Annotated[List, operator.add]
    query: str
    sql_query: str
    context: str
    response: str

# COMMAND ----------

# MAGIC %md
# MAGIC ## Node 1: SQL Query Generator

# COMMAND ----------

def generate_sql_query(state: ChatState) -> ChatState:
    """Generate SQL query based on user question."""
    user_query = state["query"]
    
    # Get conversation context for follow-up questions
    context_summary = ""
    if len(state["messages"]) > 2:
        recent = state["messages"][-4:]  # Last 2 Q&A pairs
        context_summary = "\n\nPrevious conversation context:\n"
        for msg in recent:
            if isinstance(msg, HumanMessage):
                context_summary += f"User asked: {msg.content}\n"
            elif isinstance(msg, AIMessage):
                # Summarize the answer
                answer_preview = msg.content[:150] + "..." if len(msg.content) > 150 else msg.content
                context_summary += f"Assistant answered: {answer_preview}\n"
        context_summary += "\nIf the current question references previous results (e.g., 'they', 'those', 'the ones'), use the context above to understand what is being referenced.\n"
    
    sql_prompt = f"""You are a SQL expert. Generate a SQL query to answer this question about customer energy usage data.

Table: {FULL_TABLE}

Available columns:
- customer_id (string) - Customer identifier
- first_name (string) - Customer first name
- last_name (string) - Customer last name
- city (string) - Customer city
- state (string) - Customer state
- plan_id (string) - Energy plan ID
- plan_name (string) - Energy plan name
- rate_per_kwh (double) - Rate per kWh
- reading_date (date) - Date of reading
- total_kwh_daily (double) - Total kWh usage for the day
- num_readings_daily (bigint) - Number of readings per day
- avg_kwh_per_reading_daily (double) - Average kWh per reading
- calculated_cost_daily (double) - Calculated daily cost
{context_summary}
Current User Question: {user_query}

Generate a SQL query that will retrieve relevant data to answer this question.
- Use proper SQL syntax for Databricks
- IMPORTANT: Always use backticks (`) around table names: {FULL_TABLE}
- If the question references previous results, use WHERE clauses to filter based on the context
- Include appropriate WHERE clauses, ORDER BY, LIMIT as needed
- Return ONLY the SQL query, no explanations or markdown
- Example format: SELECT * FROM `na-dbxtraining`.biju_gold.gold_daily_customer_kwh_summary WHERE ...

SQL Query:"""

    try:
        # Use Foundation Model API - adjust model name based on your workspace
        # Common options: "databricks-meta-llama-3-70b-instruct", "databricks-mixtral-8x7b-instruct", etc.
        # Or use a custom endpoint name if you have one deployed
        llm = ChatDatabricks(
            endpoint=LLM_ENDPOINT,  # Use configured endpoint
            temperature=0.1
        )
        
        response = llm.invoke(sql_prompt)
        sql_query = response.content.strip()
        
        # Clean up SQL query (remove markdown code blocks if present)
        if sql_query.startswith("```sql"):
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        elif sql_query.startswith("```"):
            sql_query = sql_query.replace("```", "").strip()
        
        # Fix table name - ensure backticks are used for catalog name
        # Replace unquoted catalog name with properly quoted version
        if "na-dbxtraining" in sql_query and "`na-dbxtraining`" not in sql_query:
            # Replace na-dbxtraining with `na-dbxtraining` if not already quoted
            sql_query = sql_query.replace("na-dbxtraining", "`na-dbxtraining`")
        
        # Ensure the correct table name is used (fix any typos like _ne suffix)
        if "gold_daily_customer_kwh_summary" in sql_query:
            # Fix any incorrect table name variations
            sql_query = sql_query.replace("gold_daily_customer_kwh_summary_ne", "gold_daily_customer_kwh_summary")
            sql_query = sql_query.replace("gold_daily_customer_kwh_summary_", "gold_daily_customer_kwh_summary")
        
        # If table name is not in the query, add it
        if FULL_TABLE not in sql_query and "FROM" in sql_query.upper():
            # Try to replace any table reference with the correct one
            import re
            # Match FROM clause and replace table name
            pattern = r'FROM\s+([^\s;]+)'
            if re.search(pattern, sql_query, re.IGNORECASE):
                sql_query = re.sub(pattern, f'FROM {FULL_TABLE}', sql_query, flags=re.IGNORECASE)
        
        print(f"📝 Generated SQL Query:\n{sql_query}\n")
        state["sql_query"] = sql_query
        
    except Exception as e:
        print(f"❌ Error generating SQL: {e}")
        state["sql_query"] = f"SELECT * FROM {FULL_TABLE} LIMIT 10"
        state["context"] = f"Error generating SQL query: {str(e)}"
    
    return state

# COMMAND ----------

# MAGIC %md
# MAGIC ## Node 2: Data Retrieval

# COMMAND ----------

def retrieve_data(state: ChatState) -> ChatState:
    """Execute SQL query and retrieve context data."""
    sql_query = state["sql_query"]
    
    try:
        print(f"🔍 Executing SQL query...")
        
        # Execute query using Spark
        df = spark.sql(sql_query)
        
        # Convert to list of dictionaries for context
        rows = df.collect()
        context_data = []
        
        # Limit to 50 rows for context to avoid token limits
        for row in rows[:50]:
            row_dict = row.asDict()
            context_data.append(row_dict)
        
        # Format context as text
        if context_data:
            context = f"Retrieved {len(context_data)} rows from the database:\n\n"
            for i, row in enumerate(context_data, 1):
                context += f"Row {i}:\n"
                for key, value in row.items():
                    context += f"  {key}: {value}\n"
                context += "\n"
        else:
            context = "No data found matching the query."
        
        state["context"] = context
        print(f"✅ Retrieved {len(context_data)} rows")
        
    except Exception as e:
        error_msg = f"Error executing SQL query: {str(e)}\n\nSQL Query:\n{sql_query}"
        print(f"❌ {error_msg}")
        state["context"] = error_msg
    
    return state

# COMMAND ----------

# MAGIC %md
# MAGIC ## Node 3: Response Generator

# COMMAND ----------

def generate_response(state: ChatState) -> ChatState:
    """Generate final response using LLM with context."""
    user_query = state["query"]
    context = state["context"]
    
    # Get recent chat history (last 10 messages for context)
    chat_history = state["messages"][-10:] if len(state["messages"]) > 10 else state["messages"]
    
    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessage(content="""You are a helpful assistant that answers questions about customer energy usage data.
Use the provided data context to answer the user's question accurately and conversationally.

Guidelines:
- Answer based ONLY on the provided context data
- If the data doesn't contain enough information, say so clearly
- Format numbers (costs, usage) in a readable way
- Be concise but informative
- If there are multiple results, summarize key findings
- Use natural, conversational language"""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", """Question: {question}

Context Data:
{context}

Please answer the question based on the context data provided above. If the context doesn't have enough information, let the user know.""")
    ])
    
    try:
        llm = ChatDatabricks(
            endpoint=LLM_ENDPOINT,  # Use configured endpoint
            temperature=0.7
        )
        
        chain = prompt_template | llm
        
        response = chain.invoke({
            "question": user_query,
            "context": context,
            "chat_history": chat_history
        })
        
        state["response"] = response.content
        state["messages"].append(HumanMessage(content=user_query))
        state["messages"].append(AIMessage(content=response.content))
        
        print(f"✅ Response generated")
        
    except Exception as e:
        error_msg = f"Error generating response: {str(e)}"
        print(f"❌ {error_msg}")
        state["response"] = error_msg
        state["messages"].append(HumanMessage(content=user_query))
        state["messages"].append(AIMessage(content=error_msg))
    
    return state


# COMMAND ----------

# MAGIC %md
# MAGIC ## Build LangGraph Workflow

# COMMAND ----------



workflow = StateGraph(ChatState)

# Add nodes
workflow.add_node("generate_sql", generate_sql_query)
workflow.add_node("retrieve_data", retrieve_data)
workflow.add_node("generate_response", generate_response)

# Define edges
workflow.set_entry_point("generate_sql")
workflow.add_edge("generate_sql", "retrieve_data")
workflow.add_edge("retrieve_data", "generate_response")
workflow.add_edge("generate_response", END)

# Compile the graph
app = workflow.compile()

print("✅ LangGraph workflow compiled successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Chatbot Function

# COMMAND ----------

def chat_with_rag(question: str, chat_history: List = None) -> tuple:
    """
    Main function to chat with RAG system.
    
    Args:
        question: User's question
        chat_history: Previous conversation messages (optional)
    
    Returns:
        tuple: (response, updated_messages)
    """
    if chat_history is None:
        chat_history = []
    
    # Initialize state
    initial_state = {
        "messages": chat_history,
        "query": question,
        "sql_query": "",
        "context": "",
        "response": ""
    }
    
    # Run the graph
    result = app.invoke(initial_state)
    
    return result["response"], result["messages"]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test the Chatbot

# COMMAND ----------

# Test query
test_question = "What are the top 5 customers in Green Energy 24 plan?"

print("=" * 80)
print(f"Test Question: {test_question}")
print("=" * 80)

response, messages = chat_with_rag(test_question)

print(f"\n📊 Response:\n{response}\n")
print("=" * 80)

# COMMAND ----------

# Test query
test_question = "Find customers named John?"

print("=" * 80)
print(f"Test Question: {test_question}")
print("=" * 80)

response, messages = chat_with_rag(test_question)

print(f"\n📊 Response:\n{response}\n")
print("=" * 80)

# COMMAND ----------

# Test query
test_question = "Compare average usage between California and New York"

print("=" * 80)
print(f"Test Question: {test_question}")
print("=" * 80)

response, messages = chat_with_rag(test_question)

print(f"\n📊 Response:\n{response}\n")
print("=" * 80)

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from `na-dbxtraining`.biju_gold.gold_daily_customer_kwh_summary where total_kwh_daily=(select max( total_kwh_daily)from `na-dbxtraining`.biju_gold.gold_daily_customer_kwh_summary)

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from `na-dbxtraining`.biju_gold.gold_daily_customer_kwh_summary where first_name like '%Diamond%'

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from `na-dbxtraining`.biju_gold.gold_daily_customer_kwh_summary

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gradio Interface (Embedded)

# COMMAND ----------

import gradio as gr
import os

def gradio_chat(message: str, history):
    """Gradio chat function."""
    if not message or not message.strip():
        return history

    try:
        # Convert Gradio history format to LangChain messages
        chat_history = []
        for human_msg, ai_msg in history:
            chat_history.append(HumanMessage(content=human_msg))
            chat_history.append(AIMessage(content=ai_msg))

        # Get response from RAG system
        response, updated_messages = chat_with_rag(message, chat_history)

        # Append to history
        history.append((message, response))

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        history.append((message, error_msg))

    return history

# Create Gradio interface
with gr.Blocks(title="Customer KWH RAG Chatbot") as demo:
    gr.Markdown("""
    # 🔌 Customer Energy Usage RAG Chatbot

    Ask questions about customer energy usage data from the `gold_daily_customer_kwh_summary` table.

    **Example questions:**
    - "What are the top 5 customers with highest daily energy usage?"
    - "Show me customers in California with daily cost over $50"
    - "Which plan has the most customers?"
    - "What's the average daily usage in New York?"
    - "Find customers with unusual energy consumption patterns"
    """)

    chatbot = gr.Chatbot(
        label="Chat",
        height=500
    )

    with gr.Row():
        msg = gr.Textbox(
            label="Your Question",
            placeholder="Ask a question about customer energy usage...",
            scale=4,
            lines=2
        )
        submit_btn = gr.Button("Send", variant="primary", scale=1)

    clear_btn = gr.Button("Clear Chat", variant="secondary")

    # Event handlers
    msg.submit(gradio_chat, [msg, chatbot], [chatbot])
    msg.submit(lambda: "", None, [msg])
    submit_btn.click(gradio_chat, [msg, chatbot], [chatbot])
    submit_btn.click(lambda: "", None, [msg])
    clear_btn.click(lambda: [], None, [chatbot])

    gr.Markdown("""
    ### 💡 Tips:
    - Be specific in your questions
    - Ask about customers, locations, plans, usage, or costs
    - The chatbot uses SQL queries to retrieve relevant data
    - Results are limited to top 50 rows for performance
    """)

# Launch Gradio interface
demo.launch(
    server_name="0.0.0.0",
    share=False,
    theme=gr.themes.Soft()
)

# COMMAND ----------



# COMMAND ----------

# MAGIC %md
# MAGIC     ### 📋 Plan Analysis
# MAGIC - "How many customers are on each plan?"
# MAGIC - "What's the average usage for Premium Energy Plan customers?"
# MAGIC - "Show me all customers on Basic Energy Plan"
# MAGIC - "Which plan has customers with highest average usage?"
# MAGIC - "Compare average costs between different plans"
# MAGIC - "What's the rate per kWh for Premium Energy Plan?"
# MAGIC
# MAGIC ### 📈 Usage Analysis
# MAGIC - "What's the average daily energy usage?"
# MAGIC - "Show me customers with usage above 100 kWh daily"
# MAGIC - "Which customers have unusual consumption patterns?"
# MAGIC - "What's the average number of readings per day?"
# MAGIC - "Show me customers with usage between 50 and 100 kWh"
# MAGIC - "What's the maximum daily usage recorded?"
# MAGIC
# MAGIC ### 🔍 Specific Customer Queries
# MAGIC - "Show me details for customer ID CUST001"
# MAGIC - "Find customers named John"
# MAGIC - "Show me all information for customers in Los Angeles"
# MAGIC - "Find customers with last name Smith"
# MAGIC
# MAGIC ### 📅 Date-Based Queries
# MAGIC - "Show me customers from the most recent reading date"
# MAGIC - "What's the average usage for the latest date?"
# MAGIC - "Show me data from the last 7 days" (if date range available)
# MAGIC
# MAGIC ### 🔄 Comparison Queries
# MAGIC - "Compare average usage between California and New York"
# MAGIC - "How does Premium plan usage compare to Basic plan?"
# MAGIC - "Compare daily costs between different states"
# MAGIC - "What's the difference in usage between top and bottom c
