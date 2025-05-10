from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import json

@dataclass
class Tool:
    name: str
    description: str
    type: str  # e.g., 'github', 'slack', 'jira', 'custom'
    config: Dict
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None

    def __post_init__(self):
        if self.type == 'http_api':
            required_fields = ['base_url', 'http_method', 'endpoint_path']
            for field in required_fields:
                if field not in self.config:
                    raise ValueError(f"Missing required field '{field}' for HTTP API tool")
            
            # Ensure headers is a dictionary
            if 'headers' not in self.config:
                self.config['headers'] = {}
            
            # Ensure body_template is a string
            if 'body_template' not in self.config:
                self.config['body_template'] = ''

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'config': self.config,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat() if self.last_used else None
        }

@dataclass
class Agent:
    name: str
    description: str
    model: str = 'meta-llama/llama-4-scout-17b-16e-instruct'
    temperature: float = 0.7
    max_tokens: int = 1024
    tools: List[Tool] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_active: Optional[datetime] = None

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'model': self.model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'tools': [tool.name if isinstance(tool, Tool) else tool for tool in self.tools],
            'created_at': self.created_at.isoformat(),
            'last_active': self.last_active.isoformat() if self.last_active else None
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data['name'],
            description=data['description'],
            model=data.get('model', 'meta-llama/llama-4-scout-17b-16e-instruct'),
            temperature=float(data.get('temperature', 0.7)),
            max_tokens=int(data.get('max_tokens', 1024)),
            tools=data.get('tools', []),  # This will be a list of tool names
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now(),
            last_active=datetime.fromisoformat(data['last_active']) if data.get('last_active') else None
        ) 