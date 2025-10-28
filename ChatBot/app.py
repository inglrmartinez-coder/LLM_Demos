import os, gradio as gr
from dotenv import load_dotenv
from openai import OpenAI

#load the envmodesl
load_dotenv()

openai_api_key= os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_APPI_KEY")
google_api_key= os.getenv("GOOGLE_API_KEY")

openai = OpenAI()
MODEL = 'gpt-4o-mini' #lets use OpenAI

#system prompt for the chat
system_promp="you are a very useful assistant"


#using this structure works for the chatinterface function 
# for the gradio interface
def chat(message,history):
    messages = [{"role":"system","content":system_promp}] + \
    history + [{"role":"user","content":message}]

    print("the history is",history)
    print("the messages is",messages)

    stream  = openai.chat.completions.create(model=MODEL,
                                             messages=messages,
                                             stream=True)

    response = ""
    for chunk in stream:
        response += chunk.choices[0].delta.content or ""
        yield response
