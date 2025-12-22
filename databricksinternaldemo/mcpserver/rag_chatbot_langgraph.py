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
# MAGIC ## Install Required Packages

# COMMAND ----------

# MAGIC %pip install langchain langchain-databricks langgraph gradio databricks-sdk databricks-langchain

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
TABLE = "gold_daily_customer_kwh_summary"
FULL_TABLE = f"`{CATALOG}`.{SCHEMA}.{TABLE}"

print(f"✅ Configuration loaded")
print(f"   Table: {FULL_TABLE}")

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

User Question: {user_query}

Generate a SQL query that will retrieve relevant data to answer this question.
- Use proper SQL syntax for Databricks
- Include appropriate WHERE clauses, ORDER BY, LIMIT as needed
- Return ONLY the SQL query, no explanations or markdown

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

# Create the graph
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
test_question = "What are the top 5 customers with highest daily energy usage?"

print("=" * 80)
print(f"Test Question: {test_question}")
print("=" * 80)

response, messages = chat_with_rag(test_question)

print(f"\n📊 Response:\n{response}\n")
print("=" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gradio Interface (Embedded)

# COMMAND ----------

import gradio as gr

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
with gr.Blocks(title="Customer KWH RAG Chatbot", theme=gr.themes.Soft()) as demo:
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
        height=500,
        show_copy_button=True
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
# In Databricks, this will be available via the notebook
try:
    port = int(os.environ.get("GRADIO_SERVER_PORT", 7860))
    demo.launch(server_port=port, server_name="0.0.0.0", share=False)
except:
    demo.launch(server_port=7860, share=False)

