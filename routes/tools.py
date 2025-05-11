from flask import Blueprint, request, jsonify
from models import Tool
from storage import Storage

tools_bp = Blueprint('tools', __name__)
storage = Storage()

@tools_bp.route('/tools', methods=['GET'])
def list_tools():
    tools = storage.load_tools()
    return jsonify([vars(tool) for tool in tools])

@tools_bp.route('/tools', methods=['POST'])
def create_tool():
    data = request.json
    tool = Tool(**data)
    tools = storage.load_tools()
    tools.append(tool)
    storage.save_tools(tools)
    return jsonify(vars(tool)), 201

@tools_bp.route('/tools/<tool_name>', methods=['DELETE'])
def delete_tool(tool_name):
    try:
        # Check if any agent is using this tool
        agents = storage.load_agents()
        agents_using_tool = [agent.name for agent in agents if tool_name in agent.tools]
        
        if agents_using_tool:
            return jsonify({
                'error': f'Cannot delete tool "{tool_name}" as it is being used by the following agents: {", ".join(agents_using_tool)}'
            }), 400

        # If no agents are using the tool, proceed with deletion
        tools = storage.load_tools()
        tools = [tool for tool in tools if tool.name != tool_name]
        storage.save_tools(tools)
        return jsonify({'message': f'Tool {tool_name} deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500 