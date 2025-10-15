import gradio as gr
from  OpenAI_Qwen.opeai_conn import stream_call_llm

def fn_shout(text:str) -> str:
    return text.upper()

#sets dark mode
force_dark_mode="""
function refresh(){
  const url = new URL(window.location);
  if (url.searchParams.get('__theme') !== 'dark'){
    url.searchParams.set('__theme','dark');
    window.location.href = url.href
  }
}
"""

#uses several inputs
gr.Interface(
    fn=stream_call_llm,
    #inputs="textbox",
    inputs=[gr.Textbox(label="Your message",lines=5), 
            gr.Dropdown(["ollama","qwen"],value="qwen",label="select a model")],
    outputs=[gr.Markdown(label="response from llm")],
    title="Shout Demo", 
    flagging_mode="never",
    js=force_dark_mode
).launch(share=True)

#options in lanch :
#share=true , create a share url that is public
#inbrowser=true, opens the app in the browser [works when you are using jupyter]
#empty, just open the app and show the local url.

#flagging_mode=never, sets the flags dissabled and store the flags in .gradio folder

    
