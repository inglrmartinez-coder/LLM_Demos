import streamlit as st
from llm_con import Config,graph

st.title(f"Chat with {Config.MODEL_NAME}")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

user_input = st.text_input("Type your message:", key="user_input")

def send_message():
    user_input = st.session_state["user_input"]
    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        with st.spinner("Thinking..."):
            state = {"messages": st.session_state["messages"]}
            response_state = graph.invoke(state)
            print("Response State => ",response_state)
            last_msg = response_state["messages"][-1]
            if hasattr(last_msg, "content"):
                st.session_state["messages"].append({"role": "assistant", "content": last_msg.content})
            else:
                st.session_state["messages"].append(last_msg)
        st.session_state["user_input"] = ""

#send the message
st.button("Send", on_click=send_message)

#if st.button("Send") and user_input:
#    send_message()
#    with st.spinner("Thinking..."):
#        state = {"messages": st.session_state["messages"]}
#        response_state = graph.invoke(state)
#        last_msg = response_state["messages"][-1]
#        if hasattr(last_msg, "content"):
#            st.session_state["messages"].append({"role": "assistant", "content": last_msg.content})
#        else:
#            st.session_state["messages"].append(last_msg)


st.write("## Conversation")
print("Current Messages :> ",st.session_state["messages"])
for msg in st.session_state["messages"][::-1]:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**LLM:** {msg['content']}")
