import json
import os
from typing import List, Dict, Optional
from datetime import datetime
from models import Agent, Tool

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class Storage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.agents_file = os.path.join(data_dir, "agents.json")
        self.tools_file = os.path.join(data_dir, "tools.json")
        self.logs_dir = os.path.join(data_dir, "logs")
        self._ensure_data_dir()
        self._initialize_files()

    def _ensure_data_dir(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)

    def _initialize_files(self):
        # Initialize agents file if it doesn't exist
        if not os.path.exists(self.agents_file):
            with open(self.agents_file, 'w') as f:
                json.dump([], f)

        # Initialize tools file if it doesn't exist
        if not os.path.exists(self.tools_file):
            with open(self.tools_file, 'w') as f:
                json.dump([], f)

    def save_agents(self, agents: List[Agent]):
        data = [agent.to_dict() for agent in agents]
        with open(self.agents_file, 'w') as f:
            json.dump(data, f, indent=2, cls=DateTimeEncoder)

    def load_agents(self) -> List[Agent]:
        try:
            if not os.path.exists(self.agents_file):
                return []
            with open(self.agents_file, 'r') as f:
                data = json.load(f)
            return [Agent.from_dict(agent_data) for agent_data in data]
        except json.JSONDecodeError:
            # If file is corrupted, reinitialize it
            self._initialize_files()
            return []

    def save_tools(self, tools: List[Tool]):
        data = [vars(tool) for tool in tools]
        with open(self.tools_file, 'w') as f:
            json.dump(data, f, indent=2, cls=DateTimeEncoder)

    def load_tools(self) -> List[Tool]:
        try:
            if not os.path.exists(self.tools_file):
                return []
            with open(self.tools_file, 'r') as f:
                data = json.load(f)
            return [Tool(**tool_data) for tool_data in data]
        except json.JSONDecodeError:
            # If file is corrupted, reinitialize it
            self._initialize_files()
            return []

    def get_agent(self, name: str) -> Optional[Agent]:
        agents = self.load_agents()
        for agent in agents:
            if agent.name == name:
                return agent
        return None

    def get_tool(self, name: str) -> Optional[Tool]:
        tools = self.load_tools()
        for tool in tools:
            if tool.name == name:
                return tool
        return None

    def save_interaction_log(self, agent_name: str, log_data: Dict):
        """Save an interaction log for an agent."""
        # Create a timestamp-based filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{agent_name}_{timestamp}.json"
        filepath = os.path.join(self.logs_dir, filename)
        
        # Add timestamp to log data
        log_data['timestamp'] = datetime.now().isoformat()
        
        # Save the log
        with open(filepath, 'w') as f:
            json.dump(log_data, f, indent=2, cls=DateTimeEncoder)

    def get_agent_logs(self, agent_name: str, limit: int = 10) -> List[Dict]:
        """Get the most recent interaction logs for an agent."""
        logs = []
        try:
            # Get all log files for this agent
            log_files = [f for f in os.listdir(self.logs_dir) 
                        if f.startswith(f"{agent_name}_") and f.endswith('.json')]
            
            # Sort by timestamp (newest first)
            log_files.sort(reverse=True)
            
            # Load the most recent logs
            for filename in log_files[:limit]:
                filepath = os.path.join(self.logs_dir, filename)
                with open(filepath, 'r') as f:
                    log_data = json.load(f)
                    logs.append(log_data)
                    
        except Exception as e:
            print(f"Error loading logs: {str(e)}")
            
        return logs 