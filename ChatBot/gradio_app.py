import gradio as gr
from app import chat

#gradio inteface made for chatbots
gr.ChatInterface(fn=chat,type="messages").launch()