from flask import Flask, render_template
import os
from groq import Groq
from dotenv import load_dotenv
from routes.tools import tools_bp
from routes.agents import agents_bp
from datetime import datetime
import json
import requests
from urllib.parse import urljoin
from string import Template
from models import Tool

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Register blueprints
app.register_blueprint(tools_bp)
app.register_blueprint(agents_bp)

# Debug: Print if API key is loaded
api_key = os.getenv("GROQ_API_KEY")
print(f"API Key loaded: {'Yes' if api_key else 'No'}")
print(f"API Key: {api_key}")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables. Please check your .env file.")

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

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 