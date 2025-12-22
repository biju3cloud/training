"""
Gradio Interface for RAG Chatbot
Standalone Gradio app that can be deployed separately
"""

import gradio as gr
from langchain_core.messages import HumanMessage, AIMessage

# Import from the notebook (when running in Databricks)
# For local execution, you would need to import the chat_with_rag function
try:
    from rag_chatbot_langgraph import chat_with_rag
    IN_DATABRICKS = True
except ImportError:
    # For local/standalone execution
    IN_DATABRICKS = False
    print("⚠️  Note: This should be run in Databricks environment")
    print("   Import the chat_with_rag function from rag_chatbot_langgraph notebook")

def gradio_chat(message: str, history):
    """Gradio chat function."""
    if not message or not message.strip():
        return history
    
    if not IN_DATABRICKS:
        history.append((message, "Please run this in Databricks environment where rag_chatbot_langgraph is available."))
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

def create_gradio_interface():
    """Create and launch Gradio interface."""
    
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
    
    return demo

if __name__ == "__main__":
    demo = create_gradio_interface()
    
    # Launch
    import os
    try:
        port = int(os.environ.get("GRADIO_SERVER_PORT", 7860))
        demo.launch(server_port=port, server_name="0.0.0.0", share=False)
    except:
        demo.launch(server_port=7860, share=False)

