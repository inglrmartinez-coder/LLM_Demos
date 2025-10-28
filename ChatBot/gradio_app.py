import gradio as gr
from app import chat

gr.ChatInterface(fn=chat,type="messages").launch()