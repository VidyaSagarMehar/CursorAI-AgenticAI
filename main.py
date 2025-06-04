from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
import json
import requests
import os
import platform

load_dotenv()
client = OpenAI()

OS_NAME = platform.system().lower()


def create_file(filename: str, content: str):
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ File '{filename}' created successfully."
    except Exception as e:
        return f"❌ Failed to create file '{filename}': {str(e)}"

def make_dir(path: str):
    try:
        os.makedirs(path, exist_ok=True)
        return f"✅ Directory '{path}' created or already exists."
    except Exception as e:
        return f"❌ Failed to create directory '{path}': {str(e)}"

def run_command(cmd: str):
    try:
        result = os.popen(cmd).read()
        return result
    except Exception as e:
        return str(e)

def get_weather(city: str):
    url = f"https://wttr.in/{city}?format=C+%t"
    response = requests.get(url)
    
    if response.status_code == 200:
        return f"The weather in {city} is {response.text.strip()}."
    return "Something went wrong while fetching the weather!"

available_tools = {
    "get_weather": get_weather,
    "run_command":  run_command,
    "create_file": create_file,
    "make_dir": make_dir,
}

SYSTEM_PROMPT = f"""
You are a helpful AI assistant specialized in resolving user queries using tools.

You work in phases: start ➝ plan ➝ action ➝ observe ➝ output.

Given the user query and available tools, plan step-by-step execution. Then, based on the plan, select the relevant tool from the available tools and perform the action by calling the tool.

Wait for the tool's observation and based on that, generate the final output.

🛑 Rules:
- Only one step at a time.
- Analyze the query carefully.
- Always use the tools via provided functions.

📁 FILE CREATION:
- DO NOT use `echo`, `touch`, or shell commands to write to files.
- Use:
  - `create_file` with `filename` and `content`
  - `make_dir` with folder path

✅ Output JSON Format:
{{
    "step": "string",
    "content": "string",
    "function": "string",     // only if step is 'action'
    "input": dict | string    // input parameters for the tool
}}

🛠 Available Tools:
- "get_weather": Takes a city name and returns the weather.
- "run_command": Executes a command string in the OS shell.
- "create_file": Creates a file with specific content.
- "make_dir": Creates a folder path recursively.

🧪 Example:

User: What is the weather in New York?

{{"step": "plan", "content": "User wants weather info of New York"}}
{{"step": "plan", "content": "Call get_weather with city name"}}
{{"step": "action", "function": "get_weather", "input": "new york"}}
{{"step": "observe", "output": "12 °C"}}
{{"step": "output", "content": "The weather in New York is 12 °C."}}
"""

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
]

while True:
    query = input("> ")
    messages.append({"role": "user", "content": query})

    while True:
        response = client.chat.completions.create(
            model="gpt-4.1",
            response_format={"type": "json_object"},
            messages=messages
        )
        
        msg_content = response.choices[0].message.content
        messages.append({"role": "assistant", "content": msg_content})

        parsed_response = json.loads(msg_content)

        if parsed_response.get("step") == "plan":
            print(f"🧠: {parsed_response['content']}")
            continue

        if parsed_response.get("step") == "action":
            tool_name = parsed_response.get("function")
            tool_input = parsed_response.get("input")
            print(f"🔨: Calling Tool :{tool_name} with input {tool_input}")
            
            if tool_name in available_tools:
                if isinstance(tool_input, dict):
                    output = available_tools[tool_name](**tool_input)
                else:
                    output = available_tools[tool_name](tool_input)

                messages.append({
                    "role": "user",
                    "content": json.dumps({"step": "observe", "output": output})
                })
                continue

        if parsed_response.get("step") == "output":
            print(f"🤖: {parsed_response['content']}")
            break
