import os,json,sys
from sqlalchemy import create_engine, text
from typing import TypedDict
from dotenv import load_dotenv
import sqlite3, pandas as pd
#from pathlib import Path
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph,START,END
from datetime import datetime as dt

from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from sqlite_db import setup_database
#from langchain_core.agents import create_react_agent


class Config:
    MODEL_NAME = "qwen3:8b"  # Adjust based on your Ollama setup
    QWEN_BASE_URL = "http://localhost:11434/v1"  #"http://localhost:11434/v1"   # Change to your Qwen endpoint
    DB_PATH = "./team_database.db"
    SHARED_FILES_PATH = "./shared_files"
    WEATHER_API_KEY = "your-weather-api-key"
    API_KEY="ollama"  # Ollama API key or identifier
    
    SQLServer="."
    SQLServer_DB="myDataBase"
    
class ChatState(TypedDict):
    messages: list[str]

#tool definitions
@tool
def database_query(query: str) -> str:
    """Execute a SQL query on the SQLite database and return results as a formatted string."""
    try:
        print(f"Executing the database query: {query}")
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()            
        cursor.execute(query)
        if query.strip().lower().startswith("select"):
            results = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
        else:            
            conn.commit()
            conn.close()
            return "executed successfully."            
        conn.close()
        if not results:
            return "No results found."
        df = pd.DataFrame(results, columns=columns)
        return df.to_string(index=False)
    except Exception as e:
        return f"Database error: {str(e)}"
    


@tool
def list_of_requirements() -> str:
    """
    Reads the file of requirements.txt and returns the list of packages
    needed to run the project.
    """
    try:
        print("Reading requirements.txt file")
        with open("requirements.txt", "r") as file:
            requirements = file.readlines()
        return "List of requirements:\n" + "".join(requirements)
    except Exception as e:
        return f"Error reading requirements.txt: {str(e)}"


@tool
def mssql_database_query(query: str) -> str:
    """
    Execute a SQL query on the Local database into SQL Server using TSQL sintaxis and return results as a formatted string.
    Uses SQLAlchemy for connection and querying, only reading the database.    

    The tables in the database are in the schema dbo. and are:
    - Deparments 
    - CategoryTypes      
    - UnitTypes
    - Employees
    - Products
    - Sales
    """
    try:
        start = dt.now()
        print(f"Executing the Local SQL database query: {query}")
        # Build the connection string for SQLAlchemy
        connection_string = (
            f"mssql+pyodbc://@{Config.SQLServer}/{Config.SQLServer_DB}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
        )
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            result = conn.execute(text(query))
            if result.returns_rows:
                rows = result.fetchall()
                columns = result.keys()
                if not rows:
                    return "No results found."
                df = pd.DataFrame(rows, columns=columns)
                end = dt.now()
                print(f"Execution time: {end-start}")
                return df.to_string(index=False)
            else:
                end = dt.now()
                print(f"Execution time: {end-start}")
                return "executed successfully."
    except Exception as e:
        return f"Database error: {str(e)}"



#raw version of the LLM instance without tools
raw_llm = init_chat_model(model=Config.MODEL_NAME, 
                      model_provider="ollama")

#llm = init_chat_model(model=Config.MODEL_NAME, 
#                      model_provider="ollama")


# Create the LLM instance and bind the tool
llm = ChatOpenAI(
    api_key=Config.API_KEY, #"ollama",
    model= Config.MODEL_NAME, #"qwen3",
    base_url=Config.QWEN_BASE_URL)

#llm = ChatOllama(
#    model= Config.MODEL_NAME, #"qwen3",
#    base_url=Config.QWEN_BASE_URL#,  #"http://localhost:11434/v1"   
#)

#attach the tool to the LLM instance
llm = llm.bind_tools([database_query,list_of_requirements,mssql_database_query])
#llm.bind_tools([database_query])   ****deprecated****

#the state of the beginning of the graph
def llm_node(state):
    response = llm.invoke(state["messages"])
    return {"messages": state["messages"] + [response]}
    #resp = ""
    #for chunk in llm.stream(state["messages"]):
    #    resp += chunk.content
    #return {"messages": state["messages"] + [resp]}

#the router function to decide the next node
def router(state):
    last_message = state["messages"][-1]
    return 'tools' if getattr(last_message,"tool_calls", None) else 'end'

tool_node = ToolNode(tools=[database_query,list_of_requirements,mssql_database_query])

#the tools node to execute the tool calls
def tools_node(state):
    result = tool_node.invoke(state)
    return {
        "messages": state["messages"] + result["messages"]
    }

#define the graph listing the nodes and the transitions
builder = StateGraph(ChatState) #list the type of the state
builder.add_node("llm", llm_node) #added the llm node
builder.add_node("tools", tools_node) #added the tools node
builder.add_edge(START, "llm") #from start to llm
builder.add_edge("tools", "llm") #from tools back to llm
#adds the conditional edges based on the router function
builder.add_conditional_edges("llm", router,{'tools':'tools','end':END}) 
#compile the graph
graph = builder.compile()

#create the db
setup_database(Config.DB_PATH)

if __name__ == "__main__":
    state = {'messages': []} #start the state with an empty list of messages
    #example of running the graph
    print("Type your question:")
    while True:
        start = dt.now()
        user_message = input(">> ")
        if user_message.lower() in ["exit","quit"]:
            break
        state["messages"].append(
            {"role":"user",
            "content":user_message}
        )
        state = graph.invoke(state)
        end = dt.now()
        print(f"Response time for the LLM {Config.MODEL_NAME} is: {end-start}")
        print(state["messages"][-1].content)