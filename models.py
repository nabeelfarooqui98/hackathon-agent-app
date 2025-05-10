from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
import json

@dataclass
class Tool:
    name: str
    description: str
    type: str  # e.g., 'github', 'slack', 'jira', 'custom'
    config: Dict
    is_active: bool = True
    created_at: datetime = datetime.now()

@dataclass
class Agent:
    name: str
    description: str
    tools: List[Tool]
    model: str = "meta-llama/llama-4-scout-17b-16e-instruct"  # updated default model
    temperature: float = 0.7
    max_tokens: int = 1024
    is_active: bool = True
    created_at: datetime = datetime.now()
    last_active: Optional[datetime] = None

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "tools": [vars(tool) for tool in self.tools],
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat() if self.last_active else None
        }

    @classmethod
    def from_dict(cls, data: Dict):
        tools = [Tool(**tool) for tool in data.get("tools", [])]
        return cls(
            name=data["name"],
            description=data["description"],
            tools=tools,
            model=data.get("model", "meta-llama/llama-4-scout-17b-16e-instruct"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 1024),
            is_active=data.get("is_active", True),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_active=datetime.fromisoformat(data["last_active"]) if data.get("last_active") else None
        ) 