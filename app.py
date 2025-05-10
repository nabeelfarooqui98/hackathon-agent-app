from flask import Flask, render_template, request, jsonify
import os
from groq import Groq
from dotenv import load_dotenv
import pathlib
from datetime import datetime
from models import Agent, Tool
from storage import Storage
import requests
from urllib.parse import urljoin
import json
from string import Template

# Load environment variables
load_dotenv(verbose=True)

app = Flask(__name__)
storage = Storage()

# Debug: Print if API key is loaded
api_key = os.getenv("GROQ_API_KEY")
print(f"API Key loaded: {'Yes' if api_key else 'No'}")
print(f"API Key: {api_key}")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables. Please check your .env file.")

# Initialize Groq client
print("Initializing Groq client")
client = Groq()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/agents', methods=['GET'])
def list_agents():
    agents = storage.load_agents()
    return jsonify([agent.to_dict() for agent in agents])

@app.route('/agents', methods=['POST'])
def create_agent():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Get existing tools by name
    tool_names = data.get('tools', [])
    tools = []
    for tool_name in tool_names:
        tool = storage.get_tool(tool_name)
        if tool:
            tools.append(tool)
        else:
            return jsonify({'error': f'Tool not found: {tool_name}'}), 404

    agent = Agent(
        name=data['name'],
        description=data['description'],
        model=data.get('model', 'meta-llama/llama-4-scout-17b-16e-instruct'),
        temperature=float(data.get('temperature', 0.7)),
        max_tokens=int(data.get('max_tokens', 1024)),
        tools=tool_names  # Store tool names instead of Tool objects
    )

    agents = storage.load_agents()
    agents.append(agent)
    storage.save_agents(agents)

    return jsonify(agent.to_dict()), 201

@app.route('/tools', methods=['GET'])
def list_tools():
    tools = storage.load_tools()
    return jsonify([vars(tool) for tool in tools])

@app.route('/tools', methods=['POST'])
def create_tool():
    data = request.json
    tool = Tool(**data)
    tools = storage.load_tools()
    tools.append(tool)
    storage.save_tools(tools)
    return jsonify(vars(tool)), 201

def execute_http_tool(tool: Tool, params: dict) -> str:
    """Execute an HTTP API tool with the given parameters."""
    try:
        # Construct the full URL
        url = urljoin(tool.config['base_url'], tool.config['endpoint_path'])
        
        # Prepare headers
        headers = tool.config['headers'].copy()
        
        # Prepare body if it exists
        body = None
        if tool.config['body_template']:
            # Replace placeholders in the template
            template = Template(tool.config['body_template'])
            body = json.loads(template.substitute(params))
        
        # Make the request
        response = requests.request(
            method=tool.config['http_method'],
            url=url,
            headers=headers,
            json=body if body else None,
            params=params if tool.config['http_method'] == 'GET' else None
        )
        
        # Update last_used timestamp
        tool.last_used = datetime.now()
        
        # Return the response
        return f"Tool '{tool.name}' executed successfully. Response: {response.text}"
    except Exception as e:
        return f"Error executing tool '{tool.name}': {str(e)}"

@app.route('/ask/<agent_name>', methods=['POST'])
def ask_agent(agent_name):
    try:
        agent = storage.get_agent(agent_name)
        if not agent:
            return jsonify({'error': f'Agent {agent_name} not found'}), 404

        question = request.json.get('question')
        if not question:
            return jsonify({'error': 'No question provided'}), 400

        # Update agent's last active timestamp
        agent.last_active = datetime.now()
        agents = storage.load_agents()
        for i, a in enumerate(agents):
            if a.name == agent_name:
                agents[i] = agent
                break
        storage.save_agents(agents)

        # Get available tools for the agent
        available_tools = []
        for tool_name in agent.tools:
            tool = storage.get_tool(tool_name)
            if tool:
                available_tools.append(tool)

        # Create a system message that includes tool information
        system_message = f"""You are an AI assistant with access to the following tools:
{json.dumps([{'name': tool.name, 'description': tool.description} for tool in available_tools], indent=2)}

When you need to use a tool, respond with a JSON object in this format:
{{
    "tool": "tool_name",
    "params": {{
        "param1": "value1",
        "param2": "value2"
    }}
}}

Otherwise, respond normally to the user's question."""

        # Get response from Groq
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            model=agent.model,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
        )

        response = chat_completion.choices[0].message.content

        # Check if the response is a tool usage request
        try:
            tool_request = json.loads(response)
            if isinstance(tool_request, dict) and 'tool' in tool_request and 'params' in tool_request:
                # Find the requested tool
                tool_name = tool_request['tool']
                tool = next((t for t in available_tools if t.name == tool_name), None)
                
                if tool:
                    # Execute the tool
                    tool_result = execute_http_tool(tool, tool_request['params'])
                    
                    # Get a final response from the AI about the tool result
                    final_response = client.chat.completions.create(
                        messages=[
                            {
                                "role": "system",
                                "content": system_message
                            },
                            {
                                "role": "user",
                                "content": question
                            },
                            {
                                "role": "assistant",
                                "content": response
                            },
                            {
                                "role": "user",
                                "content": f"Tool execution result: {tool_result}"
                            }
                        ],
                        model=agent.model,
                        temperature=agent.temperature,
                        max_tokens=agent.max_tokens,
                    )
                    response = final_response.choices[0].message.content
                else:
                    response = f"Error: Tool '{tool_name}' not found or not available to this agent."
        except json.JSONDecodeError:
            # Response is not a tool usage request, use it as is
            pass

        return jsonify({'response': response})

    except Exception as e:
        print(f"Error in /ask endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 