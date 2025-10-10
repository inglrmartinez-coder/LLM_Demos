from fastmcp import Client
#from fastmcp.client.transports import StdioTransport
from openai import OpenAI
import json, asyncio, enum

# Define your enums here
class CallType(enum.Enum):    
    tool = "function"   
    prompt = "prompt"
    resource = "resource"

# Connect to your MCP server
tool_client = Client("http://localhost:5000/mcp")
#local_client = Client("mcp_app.py")  # For internal calls if needed

# Connect to Qwen via Ollama
llm = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

#lst = asyncio.run(tool_client.list_tools())

async def test():
    async with tool_client:
        lst = await tool_client.list_tools()
    print("Available tools from MCP server:", lst)
 
async def test_call():
    async with tool_client as client:
        await client.ping()                
        tools = await client.list_tools()        
        resources = await client.list_resources()
        prompts = await client.list_prompts()
        result = await tool_client.call_tool_mcp("get_weather", {"city": "new_york"})
        
        print("Tools:", tools)
        print("Resources:", resources)
        print("Prompts:", prompts)
        print("Result of get_weather:", result)
        
async def test_call_local():
    #transport = StdioTransport(command="python", args=["mcp_app.py"])
    #async with Client(transport) as client:
    async with Client("server.py") as client:
        await client.ping()        
        result = await tool_client.call_tool_mcp("get_weather", {"city": "london"})
        print("Result of get_weather from local MCP:", result)
        
#asyncio.run(test_call())
#asyncio.run(test_call_local())

# Simple tool routing logic
async def route_tool_call(tool_name, args):
    async with tool_client:        
        ty = None
        tools = await tool_client.list_tools()
        resources = await tool_client.list_resources()
        prompts = await tool_client.list_prompts()
        if tool_name in [tool.name for tool in tools]:#
            ty= CallType.tool
            result = await tool_client.call_tool_mcp(tool_name, args)
        elif tool_name in [resource.name for resource in resources]:#
            ty= CallType.resource
            url_resource = list(filter(lambda x: x.name==tool_name,resources))[0]
            result = await tool_client.read_resource_mcp(str(url_resource.uri))            
        elif tool_name in [prompt.name for prompt in prompts]:#
            ty= CallType.prompt
            result = await tool_client.get_prompt_mcp(tool_name, args)        
        #result = await tool_client.call_tool_mcp(tool_name, args)  # Log the call
        #if "contents" in result:
        if hasattr(result, "contents"):
            return {"type":ty,"result": result.contents[0].text}
        elif hasattr(result, "content"):
            return {"type":ty,"result": result.content[0].text}
        elif hasattr(result, "messages"):
            return {"type":ty,"result": result.messages[0].content.text}
    #return tool_client.call(tool_name, args)

# Chat loop
print("🌤️ Weather Chat Agent (type 'exit' to quit)")
history = []


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather info for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_cities",
            "description": "List available cities",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_city",
            "description": "Add a new city with weather data",
            "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "temp": {"type": "integer"},
                "condition": {"type": "string"},
                "humidity": {"type": "integer"}
            },
            "required": ["city", "temp", "condition", "humidity"]
        }
    }},
    {
        "type": "function",
        "function": {
            "name": "get_current_weather_data",
            "description": "Get all current weather data in JSON format",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_prompt",
            "description": "Get city prompt for a specific city when the name of the city is provided",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"}
                },
                "required": ["city"]
            }
        }
    },
    
]

async def call_llm(messages, stream_mode=False):
    if stream_mode:
        stream_data = llm.chat.completions.create(model="qwen3:8b", messages=messages, tools=tools, stream=True)
        response = ""
        for st in stream_data:
            response += st.choices[0].delta.content if hasattr(st.choices[0].delta, "content") else ""
        return response
    else:
        response = llm.chat.completions.create(model="qwen3:8b",
                                               messages=messages,
                                               tools=tools,
                                               tool_choice="auto")
        if not response.choices[0].message.tool_calls:
            #return {"messages": messages + [{"role": "assistant", "content": response.choices[0].message.content}]}
            #return messages.append({"role": "assistant", "content": response.choices[0].message.content})
            return response.choices[0].message.content
        else:
            tool_calls = response.choices[0].message.tool_calls
            if tool_calls:
                for tool_call in [tool_calls[0]]:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    # Execute the tool manually
                    result = await route_tool_call(function_name, arguments)
                if result["type"] == CallType.prompt:                    
                    #messages.append({"role": "user", "content": result["result"]})
                    nw_messages= [{"role": "assistant", "content": result["result"]}]
                    follow_up = await call_llm(nw_messages, stream_mode)
                    return follow_up
                    #return {"messages": messages + [{"role": "assistant", "content": follow_up}]}
                    #follow_up = llm.chat.completions.create(
                    #    model="qwen3:8b",
                    #    messages=messages
                    #)
                    #return messages.append({"role": "assistant", "content": follow_up.choices[0].message.content})
                    #return follow_up.choices[0].message.content
                else:
                    #return messages.append({"role": "assistant", "content": result["result"]})
                    return result["result"]
            else:
                #return messages.append({"role": "assistant", "content": response.choices[0].message.content})
                return response.choices[0].message.content
            #return {messages + [{"role": "assistant", "content": follow_up.choices[0].message.content}]}
        #return response.choices[0].message.content


async def main():
    history = []
    history.append({"role": "system", "content": "You are a helpful weather assistant. You can call tools like get_weather, list_cities, add_city."})
    while True:
        user_input = input("👤 You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break
        history.append({"role": "user", "content": user_input})
        response = await call_llm(history, stream_mode=False)
        history.append({"role": "assistant", "content": response})
        print(f"🤖 Agent: {history[-1]['content']}")         
            
if __name__ == "__main__":
    #main()
    asyncio.run(main())
    
    
"""
        # Call Qwen to decide what to do
        response = llm.chat.completions.create(
            model="qwen3:8b",
            messages=[
                {"role": "system", "content": "You can call tools like get_weather, list_cities, add_city."},
                *history
            ],
            tools=tools,            
            tool_choice="auto"
        )

        msg = response.choices[0].message
        if msg.tool_calls:
            for call in msg.tool_calls:
                tool_name = call.function.name
                args = json.loads(call.function.arguments)
                result = await route_tool_call(tool_name, args)
                history.append({"role": "tool", "tool_name": tool_name, "content": result})
                print(f"🔧 Tool: {result}")
        else:
            history.append({"role": "assistant", "content": msg.content})
            print(f"🤖 Agent: {msg.content}")
    
    
    follow_up = llm.chat.completions.create(
                    model="qwen3:8b",
                    messages=messages + [
                        response.choices[0].message,
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": result
                        }
                ])
                """