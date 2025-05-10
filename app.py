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

def execute_http_tool(tool: Tool, params: dict) -> tuple[str, dict]:
    """Execute an HTTP API tool with the given parameters.
    Returns a tuple of (response_text, debug_info)"""
    debug_info = {
        'timestamp': datetime.now().isoformat(),
        'tool_name': tool.name,
        'request': {
            'method': tool.config['http_method'],
            'base_url': tool.config['base_url'],
            'endpoint_path': tool.config['endpoint_path'],
            'combined_url': urljoin(tool.config['base_url'], tool.config['endpoint_path']),
            'headers': tool.config['headers'],
            'params': params
        }
    }
    
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
            debug_info['request']['body'] = body
        
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
        
        # Add response info to debug
        debug_info['response'] = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'text': response.text[:1000] + '...' if len(response.text) > 1000 else response.text
        }
        
        # Return both response and debug info
        return f"Tool '{tool.name}' executed successfully. Response: {response.text}", debug_info
    except Exception as e:
        debug_info['error'] = str(e)
        return f"Error executing tool '{tool.name}': {str(e)}", debug_info

@app.route('/ask/<agent_name>', methods=['POST'])
def ask_agent(agent_name):
    try:
        agent = storage.get_agent(agent_name)
        if not agent:
            return jsonify({'error': f'Agent {agent_name} not found'}), 404

        data = request.get_json()
        question = data.get('question')
        debug_mode = data.get('debug', False)  # Only used for frontend display
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400

        debug_log = []
        tools_used = []  # Track tools used in this interaction

        debug_log.append({
            'timestamp': datetime.now().isoformat(),
            'event': 'request_received',
            'question': question
        })

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

        debug_log.append({
            'timestamp': datetime.now().isoformat(),
            'event': 'tools_loaded',
            'available_tools': [tool.name for tool in available_tools]
        })

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

        debug_log.append({
            'timestamp': datetime.now().isoformat(),
            'event': 'groq_api_call',
            'model': agent.model,
            'temperature': agent.temperature,
            'max_tokens': agent.max_tokens
        })

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

        debug_log.append({
            'timestamp': datetime.now().isoformat(),
            'event': 'groq_response_received',
            'response': response
        })

        # Check if the response is a tool usage request
        try:
            tool_request = json.loads(response)
            if isinstance(tool_request, dict) and 'tool' in tool_request and 'params' in tool_request:
                debug_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'event': 'tool_request_detected',
                    'tool_request': tool_request
                })

                # Find the requested tool
                tool_name = tool_request['tool']
                tool = next((t for t in available_tools if t.name == tool_name), None)
                
                if tool:
                    tools_used.append(tool_name)  # Add tool to used tools list
                    
                    debug_log.append({
                        'timestamp': datetime.now().isoformat(),
                        'event': 'tool_execution_started',
                        'tool': tool_name,
                        'params': tool_request['params']
                    })

                    # Execute the tool
                    tool_result, tool_debug = execute_http_tool(tool, tool_request['params'])
                    
                    debug_log.append({
                        'timestamp': datetime.now().isoformat(),
                        'event': 'tool_execution_completed',
                        'tool': tool_name,
                        'result': tool_result,
                        'debug_info': tool_debug
                    })

                    debug_log.append({
                        'timestamp': datetime.now().isoformat(),
                        'event': 'groq_api_call',
                        'model': agent.model,
                        'temperature': agent.temperature,
                        'max_tokens': agent.max_tokens,
                        'context': 'tool_result_interpretation'
                    })

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

                    debug_log.append({
                        'timestamp': datetime.now().isoformat(),
                        'event': 'groq_response_received',
                        'response': response,
                        'context': 'tool_result_interpretation'
                    })
                else:
                    response = f"Error: Tool '{tool_name}' not found or not available to this agent."
                    debug_log.append({
                        'timestamp': datetime.now().isoformat(),
                        'event': 'tool_not_found',
                        'tool': tool_name
                    })
        except json.JSONDecodeError:
            # Response is not a tool usage request, use it as is
            debug_log.append({
                'timestamp': datetime.now().isoformat(),
                'event': 'no_tool_request',
                'response': response
            })

        # Save the interaction log
        log_data = {
            'agent_name': agent_name,
            'question': question,
            'response': response,
            'tools_used': tools_used,
            'debug_log': debug_log
        }
        storage.save_interaction_log(agent_name, log_data)

        return jsonify({
            'response': response,
            'tools_used': tools_used,
            'debug_log': debug_log
        })

    except Exception as e:
        print(f"Error in /ask endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/recommend_agent', methods=['POST'])
def recommend_agent():
    try:
        data = request.get_json()
        question = data.get('question')
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400

        # Get all agents
        agents = storage.load_agents()
        
        if not agents:
            return jsonify({'error': 'No agents available'}), 404

        # Create a system message for agent selection
        system_message = """You are an AI assistant that helps select the most appropriate agent for a given question.
You will be given a list of available agents and their capabilities.
Your task is to analyze the question and select the most suitable agent.
You must respond with a valid JSON object in this exact format:
{
    "selected_agent": "agent_name",
    "reason": "explanation of why this agent is the best choice"
}

Do not include any other text or explanation outside the JSON object."""

        # Create the prompt with agent information
        agent_info = json.dumps([{
            'name': agent.name,
            'description': agent.description,
            'tools': agent.tools
        } for agent in agents], indent=2)

        prompt = f"""Available agents:
{agent_info}

Question: {question}

Which agent would be most suitable for this question? Respond with a JSON object only."""

        # Get recommendation from Groq
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.3,
            max_tokens=1024,
        )

        response_text = chat_completion.choices[0].message.content.strip()
        
        # Try to parse the response as JSON
        try:
            recommendation = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response: {str(e)}")
            print(f"Raw response: {response_text}")
            # If parsing fails, try to extract JSON from the response
            try:
                # Look for JSON-like structure in the response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    recommendation = json.loads(json_match.group())
                else:
                    raise ValueError("No JSON object found in response")
            except Exception as e:
                print(f"Error extracting JSON: {str(e)}")
                # If all parsing attempts fail, use the first available agent
                return jsonify({
                    'agent': agents[0].name,
                    'reason': f"Default agent selected due to parsing error. Original error: {str(e)}"
                })

        # Verify the response has the required fields
        if not isinstance(recommendation, dict) or 'selected_agent' not in recommendation:
            # If response is invalid, use the first available agent
            return jsonify({
                'agent': agents[0].name,
                'reason': "Default agent selected due to invalid response format"
            })
        
        # Verify the recommended agent exists
        selected_agent = next((agent for agent in agents if agent.name == recommendation['selected_agent']), None)
        if not selected_agent:
            # If recommended agent doesn't exist, use the first available agent
            return jsonify({
                'agent': agents[0].name,
                'reason': f"Default agent selected. Recommended agent '{recommendation['selected_agent']}' not found"
            })

        return jsonify({
            'agent': selected_agent.name,
            'reason': recommendation.get('reason', 'No reason provided')
        })

    except Exception as e:
        print(f"Error in /recommend_agent endpoint: {str(e)}")
        # If any other error occurs, use the first available agent
        try:
            agents = storage.load_agents()
            if agents:
                return jsonify({
                    'agent': agents[0].name,
                    'reason': f"Default agent selected due to error: {str(e)}"
                })
        except:
            pass
        return jsonify({'error': str(e)}), 500

@app.route('/agents/<agent_name>', methods=['DELETE'])
def delete_agent(agent_name):
    try:
        agents = storage.load_agents()
        # Find and remove the agent
        agents = [agent for agent in agents if agent.name != agent_name]
        storage.save_agents(agents)
        return jsonify({'message': f'Agent {agent_name} deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 