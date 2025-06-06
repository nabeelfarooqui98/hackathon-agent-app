from datetime import datetime
import json
import requests
from urllib.parse import urljoin
from string import Template
from models import Tool

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
            'headers': tool.config['headers'],
            'params': params
        }
    }
    
    try:
        # Replace path parameters in endpoint_path
        endpoint_path = tool.config['endpoint_path']
        for param_name, param_value in params.items():
            placeholder = f"<{param_name}>"
            if placeholder in endpoint_path:
                endpoint_path = endpoint_path.replace(placeholder, str(param_value))
                # Remove the used parameter from params to avoid duplicate in query string
                params = {k: v for k, v in params.items() if k != param_name}
        
        # Construct the full URL
        url = urljoin(tool.config['base_url'], endpoint_path)
        debug_info['request']['endpoint_path'] = endpoint_path
        debug_info['request']['combined_url'] = url
        
        # Prepare headers with default User-Agent
        headers = tool.config['headers'].copy()
        headers['User-Agent'] = 'Mozilla/5.0'
        headers['Accept'] = 'application/json'
        
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