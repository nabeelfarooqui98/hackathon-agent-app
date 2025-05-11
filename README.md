# ToolMind

ToolMind is an advanced AI agent orchestration platform that enables the creation and management of AI agents with tool-using capabilities. It provides a user-friendly interface for building, configuring, and interacting with AI agents that can leverage various tools to perform complex tasks.

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

## Development

The project uses:
- Flask for the backend API
- Bootstrap for the frontend UI
- Groq for LLM capabilities
- Docker for containerization

## License

MIT License 