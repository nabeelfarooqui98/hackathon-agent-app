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
        self._ensure_data_dir()
        self._initialize_files()

    def _ensure_data_dir(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

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