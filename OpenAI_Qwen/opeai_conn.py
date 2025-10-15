#from qwen_agent_example import Config
from openai import OpenAI
from datetime import datetime as dt
import sqlite3, json, pandas as pd,requests
from sqlalchemy import create_engine,text
from bs4 import BeautifulSoup
import asyncio


class Config:
    MODEL_NAME = "qwen3:8b"  # Adjust based on your Ollama setup
    QWEN_BASE_URL = "http://localhost:11434/v1"  #"http://localhost:11434/v1"   # Change to your Qwen endpoint
    DB_PATH = "./team_database.db"
    SHARED_FILES_PATH = "./shared_files"
    WEATHER_API_KEY = "your-weather-api-key"
    API_KEY="ollama"  # Ollama API key or identifier    
    SQLServer="."
    SQLServer_DB="myDataBase"




#create the client for the OpenAI API
client = OpenAI(api_key=Config.API_KEY,base_url=Config.QWEN_BASE_URL)

#openai = OpenAI(api_key=Config.MODEL_NAME,base_url=Config.QWEN_BASE_URL)
#resp = openai.chat.completions.create(model=Config.MODEL_NAME,messages=[{"role":"user","content":"Hello"}])
#print("Test response from the model: ",resp.choices[0].message.content)

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

def local_database_query(query: str) -> str:
    """
    Execute a SQL query on the local database into SQL Server using TSQL sintaxis and return results as a formatted string.
    Uses SQLAlchemy for connection and querying.
    The field CompanyCode, companyid does not exist, is always the field company.

    The tables in the database are in the schema dbo. and are:
    - Company 
    - CategoryTypes    
    - UnitTypes
    - PeriodTypes
    """
    try:
        start = dt.now()
        print(f"Executing the Local database query: {query}")
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

def read_webpage(url: str) -> str:
    """
    Fetches the content of a webpage given its URL.
    """
    
    try:
        print(f"Fetching content from URL: {url}")
        response = requests.get(url)        
        if response.status_code == 200:
            bs = BeautifulSoup(response.text, 'html.parser')
            unneded = bs(['script', 'style',"image","input"])
            if bs.body:
                for noneeded in bs.body(unneded):
                    noneeded.decompose()
                #response = bs.body.get_text(separator="\n",strip=True)              
            # Cleaned text
            response = bs.get_text(separator='\n', strip=True)  
            links = [link.get("href") for link in bs.find_all("a")]
            return response + "\n\nLinks on the page:\n" + "\n".join([link for link in links if link])
            #return response.text[:4000]  # Limit to first 4000 characters
        else:
            return f"Failed to retrieve webpage. Status code: {response.status_code}"
    except Exception as e:
        return f"Error fetching webpage: {str(e)}"

#tools = [database_query,list_of_requirements,local_database_query,read_webpage]

#read_webpage("https://www.kotaku.co.jp/")

tools = [
    {
        "type": "function",
        "function": {
            "name": "database_query",
            "description": "Execute a SQL query to SQLite database and return the result",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL query to execute"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_of_requirements",
            "description": "Returns the list of packages needed to run the project.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "local_database_query",
            "description": "Execute a SQL query on the Local database into SQL Server using TSQL sintaxis and return results as a formatted string. Uses SQLAlchemy for connection and querying.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",     
        "function": {
            "name": "read_webpage",
            "description": "Fetches the content of a webpage given its URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the webpage to fetch"
                    }
                },
                "required": ["url"]
            }
        }
    }
]

tools_dict = {"database_query": database_query,
              "list_of_requirements": list_of_requirements,
              "local_database_query": local_database_query,
              "read_webpage": read_webpage}


def stream_call_llm(message,model):
    state = {'messages': []} 
    state["messages"].append(
            {"role":"user",
            "content":message})
    if model == "qwen":
        md = Config.MODEL_NAME
    elif model == "ollama":
        md = "llama3.2"
    
    print(state)
    stream_data = client.chat.completions.create(model=md,
                                                 messages=state["messages"],
                                                 tools=tools,stream=True)
    response = ""
    for st in stream_data:
        response += st.choices[0].delta.content if hasattr(st.choices[0].delta,"content") else ""
        yield response


def call_llm(messages,stream_mode=False):
    if stream_mode:
        stream_data = client.chat.completions.create(model=Config.MODEL_NAME,messages=messages,tools=tools,stream=True)
        response = ""
        for st in stream_data:
            response += st.choices[0].delta.content if hasattr(st.choices[0].delta,"content") else ""
        return response
    else:
        response = client.chat.completions.create(model=Config.MODEL_NAME,
                                                  messages=messages,
                                                  tools=tools,
                                                  tool_choice="auto")
        if not response.choices[0].message.tool_calls:
            return {"messages": messages + [{"role": "assistant", "content": response.choices[0].message.content}]}
        else:
            tool_calls = response.choices[0].message.tool_calls
            if tool_calls:
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    # Execute the tool manually
                    result = tools_dict[function_name](**arguments)
            follow_up = client.chat.completions.create(
                        model=Config.MODEL_NAME,
                        messages=messages + [
                            response.choices[0].message,
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": function_name,
                                "content": result
                            }
                        ])
            return {"messages": messages + [{"role": "assistant", "content": follow_up.choices[0].message.content}]}
        #return response.choices[0].message.content

def test_tool_call():
    response = client.chat.completions.create(
                model=Config.MODEL_NAME,
                messages=[{"role": "user", "content": "List all employees from sqlite database"}],
                tools=tools,
                tool_choice="auto")
    
    tool_calls = response.choices[0].message.tool_calls
    if tool_calls:
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            # Execute the tool manually
            #if function_name == "database_query":
            #    result = database_query(**arguments)
            result = tools_dict[function_name](**arguments)
    
    follow_up = client.chat.completions.create(
                model=Config.MODEL_NAME,
                messages=[
                    {"role": "user", "content": "List all employees"},
                    response.choices[0].message,
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": result
                    }
                ])
    print("Final response from the LLM: ",follow_up.choices[0].message.content)


#asyncio.run(stream_call_llm("hi"))

if __name__ == "__main__":
    #test_tool_call()
    

    #es = stream_call_llm("test message")
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
        state = call_llm(state["messages"],False)  
        #client.chat.completions.create(model=Config.MODEL_NAME,messages=state["messages"])
        #resp = ""
        #for st in stream_data:
        #    resp += st.content
        end = dt.now()
        print(f"Response time for the LLM {Config.MODEL_NAME} is: {end-start}")
        print(state["messages"][-1]["content"])
