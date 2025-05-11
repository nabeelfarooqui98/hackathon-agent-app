# ToolMind

ToolMind is a simple AI agent orchestration platform that enables the creation and management of AI agents with tool-using capabilities. It provides a user-friendly interface for building, configuring, and interacting with AI agents that can leverage various tools to perform complex tasks.

*This project was created for learning purposes.*

## Features

- **Agent Management**
  - Create and configure AI agents with custom models
  - Set temperature and token limits for fine-tuned responses
  - Assign specific tools to agents based on their capabilities
  - Automatic agent recommendation based on query context

- **Tool Integration**
  - HTTP API tool support for external service integration
  - Customizable request configurations (headers, body templates)
  - Path parameter support for dynamic API endpoints
  - Tool usage tracking and debugging

- **Interactive Chat Interface**
  - Real-time agent responses with tool usage information
  - Debug mode for detailed execution logs
  - Automatic agent selection based on query context

- **User-Friendly UI**
  - Bootstrap-based responsive design
  - Tabbed interface for easy navigation
  - Real-time updates and feedback
  - Intuitive tool and agent management

## Prerequisites

- Docker and Docker Compose
- Pipenv (for local development)
- Groq API key (get it from [Groq's website](https://console.groq.com/))

## Setup

1. Clone this repository
2. Create a `.env` file in the root directory with your Groq API key:
   ```
   GROQ_API_KEY=your_api_key_here
   ```

## Running the Application

### Using Docker (Recommended)

1. Build and start the containers:
   ```bash
   docker-compose up --build
   ```

2. Access the application at `http://localhost:5000`

### Running Locally with Pipenv

1. Install dependencies using Pipenv:
   ```bash
   pipenv install
   ```

2. Activate the virtual environment:
   ```bash
   pipenv shell
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Access the application at `http://localhost:5000`

## Usage

The application comes with pre-configured sample agents and tools to help you get started.

1. **Creating Agents**
   - Navigate to the Agents tab
   - Fill in the agent details (name, description, model)
   - Configure temperature and token limits
   - Select tools for the agent to use

2. **Adding Tools**
   - Go to the Tools tab
   - Create new HTTP API tools with custom configurations
   - Set up headers, body templates, and endpoint paths

3. **Chatting with Agents**
   - Use the Chat tab to interact with agents
   - Type your question or request
   - View the agent's response and tool usage
   - Enable debug mode for detailed execution logs

   Example questions:
   - "Tell me a dad joke"
   - "What is a good dog fact?"
   - "What does the word baffled mean?"

## Limitations

- **Tool Support**
  - Currently only supports HTTP API calling tools
  - Tested primarily with GET APIs
  - No built-in support for authentication mechanisms
  - Limited to basic HTTP request/response patterns

- **Agent Capabilities**
  - Agents can only use one tool per query
  - No support for tool chaining or sequential tool execution
  - Agents cannot combine multiple tools in a single response

- **Integration Constraints**
  - Tools and agents cannot be chained together
  - No support for complex workflows or multi-step operations
  - Limited to single-step tool execution

## Future Work

- **MCP Server Integration**
  - Add support for Model Context Protocol (MCP) servers
  - Enable seamless integration with existing MCP implementations
  - Support for MCP tool definitions and execution

- **Framework Migration**
  - Migrate to LangChain or similar AI framework
  - Replace direct LLM interactions with framework abstractions
  - Leverage framework features for better tool management
  - Improved prompt engineering and chain management

- **Enhanced Tool Support**
  - Add support for authentication mechanisms
  - Implement tool chaining capabilities
  - Support for complex workflows and multi-step operations
  - Integration with more tool types beyond HTTP APIs

- **Agent Improvements**
  - Enable multi-tool usage in single queries
  - Support for agent chaining and collaboration
  - Enhanced context management and memory
  - Better error handling and recovery mechanisms

## Development

The project uses:
- Flask for the backend API
- Bootstrap for the frontend UI
- Groq for LLM capabilities
- Docker for containerization

## License

MIT License 