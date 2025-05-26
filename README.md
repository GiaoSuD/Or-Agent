# OR_Agent_TTS

Operations Research Agent with Text-to-Solution capabilities. This project uses large language models (LLMs) to solve operations research optimization problems by generating and executing Gurobi code.

## Features

- Automatic mathematical model formulation from natural language problem descriptions
- Gurobi code generation and execution
- Error handling and code correction
- Support for multiple LLM providers (OpenAI, Claude, Ollama)
- Asynchronous processing for batch operations
- Interactive visualization mode
- MCP (Model Context Protocol) server for API access

## Prerequisites

- Python 3.8 or higher
- Gurobi Optimizer (with a valid license)
- Access to LLM APIs (OpenAI, Claude) or Ollama for local models

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/OR_Agent_TTS.git
cd OR_Agent_TTS
```

### 2. Create a virtual environment

```bash
# Using venv
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Copy the example environment file and edit it with your API keys:

```bash
cp .env.example .env
```

Edit the `.env` file with your API keys:

```
# OpenAI API configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1

# Anthropic API configuration
CLAUDE_API_KEY=your_claude_api_key_here

# Ollama API configuration (optional, for local models)
OLLAMA_API_BASE=http://localhost:11434
```

## Usage

### Basic Usage

Run the agent with a specific model:

```bash
python or_llm_eval.py --agent --model o3-mini
```

### Using Different Models

You can specify different models:

```bash
# Using OpenAI models
python or_llm_eval.py --agent --model gpt-4

# Using Claude models
python or_llm_eval.py --agent --model claude-3-opus-20240229

# Using Ollama models (local)
python or_llm_eval.py --agent --model ollama:llama2
```

### Asynchronous Processing

For batch processing multiple problems:

```bash
python or_llm_eval_async.py --agent --model o3-mini
```

### Interactive Visualization

For a more interactive experience with real-time output:

```bash
python or_llm_show.py
```

## Running the MCP Server

The Model Context Protocol (MCP) server allows you to expose the OR agent functionality as an API that can be used by other applications.

### 1. Install MCP dependencies

```bash
pip install fastmcp
```

### 2. Run the MCP server

```bash
python mcp_server.py
```

This will start the MCP server on the default port (8000). You can access the API documentation at `http://localhost:8000/docs`.

### 3. Using the MCP API

You can now make requests to the MCP server:

```python
import requests

response = requests.post(
    "http://localhost:8000/tools/get_operation_research_problem_answer",
    json={
        "user_question": "A company produces two products, A and B. Each product requires processing on two machines. Product A requires 2 hours on machine 1 and 1 hour on machine 2. Product B requires 1 hour on machine 1 and 3 hours on machine 2. Machine 1 is available for 40 hours per week, and machine 2 is available for 60 hours per week. The profit is $3 per unit of product A and $4 per unit of product B. How many units of each product should be produced to maximize profit?"
    }
)

print(response.json())
```

### 4. Integrating with LLM Agents

The MCP server can be integrated with LLM agents that support the Model Context Protocol. This allows the agent to use the OR solver as a tool.

## Using Ollama for Local Models

For instructions on using Ollama with this codebase, see [OLLAMA_USAGE.md](OLLAMA_USAGE.md).

## Project Structure

- `or_llm_eval.py`: Main script for running the OR agent
- `or_llm_eval_async.py`: Asynchronous version for batch processing
- `or_llm_show.py`: Interactive visualization version
- `utils.py`: Utility functions
- `mcp_server.py`: MCP server implementation
- `data/`: Directory containing datasets and processing scripts

## Troubleshooting

### Gurobi License Issues

If you encounter Gurobi license issues, make sure you have a valid license and it's properly installed. See the [Gurobi documentation](https://www.gurobi.com/documentation/current/quickstart_windows/obtaining_a_gurobi_license.html) for more information.

### API Connection Issues

If you're having trouble connecting to the LLM APIs, check your API keys and internet connection. For Ollama, make sure the Ollama service is running.

### MCP Server Issues

If the MCP server fails to start, check that you have the required dependencies installed and that the port is not already in use.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
