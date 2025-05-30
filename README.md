# OR_Agent

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
- Access to LLM APIs (OpenAI, Claude, Gemini) or Ollama for local models

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/jasMie410/OR_Agent.git
cd OR_Agent
```


### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Copy the example environment file and edit it with your API keys:

```bash
cp .env.example .env
```

Make sure to set up the `.env` file with your API keys:

```
# OpenAI API configuration
OPENAI_API_KEY="your_openai_api_key"
OPENAI_API_BASE="your_openai_api_base"

# Gemini API configuration
GEMINI_API_KEY="your_gemini_api_key"

# Anthropic API configuration
CLAUDE_API_KEY="your_claude_api_key"

# Ollama API configuration (optional, for local models)
OLLAMA_API_BASE=http://localhost:11434

# Default model 
DEFAULT_MODEL="your_default_model"

```

## Usage

### Basic Usage

Run the agent with a specific model:

```bash
python eval.py --agent --model o3-mini
```

### Using Different Models

You can specify different models:

```bash
# Using OpenAI models
python eval.py --agent --model o3-mini

# Using Claude models
python eval.py --agent --model claude-3-opus-20240229

# Using Gemini models
python eval.py --agent --model gemini-2.0-flash

# Using Ollama models (local)
python eval.py --agent --model ollama:llama2
```

### 3. Using the MCP API

You can now make requests to the MCP server:

```bash
python mcp_server.py
```

Open another terminal then run:

```bash
python app.py
```

### 4. Integrating with LLM Agents

The MCP server can be integrated with LLM agents that support the Model Context Protocol. This allows the agent to use the OR solver as a tool.

## Using Ollama for Local Models

For instructions on using Ollama with this codebase, see [OLLAMA_USAGE.md](OLLAMA_USAGE.md).

## Project Structure

- `eval.py`: Script for running validate the OR agent
- `utils.py`: Utility functions (methods)
- `mcp_server.py`: MCP server implementation
- `app.py` : UI
- `data/`: Directory containing datasets and processing scripts

## Troubleshooting

### Gurobi License Issues

If you encounter Gurobi license issues, make sure you have a valid license and it's properly installed. See the [Gurobi documentation](https://www.gurobi.com/documentation/current/quickstart_windows/obtaining_a_gurobi_license.html) for more information.

### API Connection Issues

If you're having trouble connecting to the LLM APIs, check your API keys and internet connection. For Ollama, make sure the Ollama service is running.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
