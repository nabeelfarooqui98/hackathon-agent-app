from flask import Flask, render_template, request, jsonify
import os
from groq import Groq
from dotenv import load_dotenv
import pathlib
from datetime import datetime
from models import Agent, Tool
from storage import Storage

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

        # Get response from Groq
        chat_completion = client.chat.completions.create(
            messages=[
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
        return jsonify({'response': response})

    except Exception as e:
        print(f"Error in /ask endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 