# Using Ollama with OR_Agent_TTS

This guide explains how to use Ollama to run large language models locally with the OR_Agent_TTS codebase.

## What is Ollama?

[Ollama](https://ollama.ai/) is an open-source tool that allows you to run large language models (LLMs) locally on your machine. It provides a simple API that's compatible with many applications and libraries.

## Installation

### 1. Install Ollama

Follow the installation instructions on the [Ollama website](https://ollama.ai/download):

- **Windows**: Download and run the installer
- **macOS**: Download and install the application
- **Linux**: Run the installation script

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. Pull the models you want to use

After installing Ollama, you need to download the models you want to use. For example:

```bash
# Pull the Llama 2 model
ollama pull llama2

# Pull the Mistral model
ollama pull mistral

# Pull the CodeLlama model (good for coding tasks)
ollama pull codellama
```

You can see the full list of available models on the [Ollama model library](https://ollama.ai/library).

### 3. Configure environment variables

Copy the provided `.env.ollama` file to `.env`:

```bash
cp .env.ollama .env
```

If you're only using Ollama (and not OpenAI or Claude), you don't need to set the API keys for those services.

## Usage

### Running with Ollama models

To use an Ollama model, prefix the model name with `ollama:` when using the `--model` parameter:

```bash
# Using the agent with Llama 2
python or_llm_eval.py --agent --model ollama:llama2

# Using the agent with CodeLlama
python or_llm_eval.py --agent --model ollama:codellama

# Using the async version with Mistral
python or_llm_eval_async.py --agent --model ollama:mistral
```

### Using the interactive visualization

The `or_llm_show.py` script provides an interactive visualization of the optimization process:

```bash
# Run with Llama 2
python or_llm_show.py --model ollama:llama2
```

## Available Ollama Models for Operations Research

Some models are better suited for operations research and mathematical optimization tasks:

- **codellama**: Good for generating code, including Gurobi code
- **llama2**: General-purpose model with good reasoning capabilities
- **mistral**: Strong reasoning and instruction-following capabilities
- **neural-chat**: Optimized for chat and instruction-following
- **wizard-math**: Specialized for mathematical reasoning (may be better for complex optimization problems)

## Troubleshooting

### Model not found

If you get an error like "Model not found", make sure you've pulled the model:

```bash
ollama pull model_name
```

### API connection issues

If you're having trouble connecting to the Ollama API:

1. Make sure Ollama is running (you should see it in your system tray or processes)
2. Verify the API URL in your `.env` file (default is `http://localhost:11434`)
3. Check if you can access the API directly: `curl http://localhost:11434/api/tags`

### Performance considerations

- Ollama models run locally on your machine, so performance depends on your hardware
- Models with fewer parameters (like Mistral 7B) will run faster than larger models
- Consider using a machine with a GPU for better performance
- You can adjust the context window and other parameters in the Ollama configuration
