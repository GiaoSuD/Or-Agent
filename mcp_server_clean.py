#!/usr/bin/env python3
"""
MCP Server for OR Agent
A simplified HTTP server with JSON-RPC support for the Operations Research Agent.
"""

import logging
import sys
import os
from aiohttp import web
import io
from contextlib import redirect_stdout
from or_llm_eval import or_llm_agent
from dotenv import load_dotenv


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
# Server configuration
SERVER_NAME = "or_llm_agent"
HOST = "127.0.0.1"
PORT = 5050

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL")


# Function to solve OR problems
def get_operation_research_problem_answer(user_question, model_name=DEFAULT_MODEL, max_attempts=3):
    """Use the agent to solve the optimization problem."""
    try:
        logger.info(f"Processing OR problem: {user_question[:50]}...")
        
        # Try to solve the problem with the real agent
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            is_solve_success, result = or_llm_agent(user_question, model_name, max_attempts)
        output = buffer.getvalue()
        
        if not output.strip():
            return "No output generated from the OR agent. Please check your question format."
        
        logger.info(f"OR problem processed successfully: {is_solve_success}")
        return output
    except Exception as e:
        logger.error(f"Error in get_operation_research_problem_answer: {str(e)}")
        
        # Check for common errors
        error_message = str(e)
        if "API key" in error_message:
            return "Error: Invalid API key. Please check your .env file and ensure the API key is correctly set."
        elif "model_not_found" in error_message or "does not exist" in error_message:
            return f"Error: Model '{model_name}' not found or you don't have access to it. Try using a different model like 'gpt-3.5-turbo'."
        elif "quota" in error_message or "exceeded" in error_message:
            return "Error: API rate limit exceeded or insufficient quota. Please check your billing details or try again later."
        else:
            return f"Error processing the optimization problem: {error_message}"

# Function for health check
def health_check():
    """Simple health check to verify the server is running."""
    return "MCP Server is running and healthy!"

# JSON-RPC handler
async def handle_jsonrpc(request):
    try:
        data = await request.json()
        
        if data.get("method") == "ping":
            return web.json_response({"jsonrpc": "2.0", "result": "pong", "id": data.get("id")})
        
        if data.get("method") == "tools/list":
            tools = [
                {
                    "name": "get_operation_research_problem_answer",
                    "description": "Use the agent to solve the optimization problem",
                    "parameters": {
                        "user_question": {"type": "string", "description": "The user's question"},
                        "model_name": {"type": "string", "description": "LLM model name to use"},
                        "max_attempts": {"type": "integer", "description": "Maximum number of attempts"}
                    }
                },
                {
                    "name": "health_check",
                    "description": "Simple health check to verify the server is running",
                    "parameters": {}
                }
            ]
            return web.json_response({"jsonrpc": "2.0", "result": tools, "id": data.get("id")})
        
        if data.get("method") == "tools/call":
            params = data.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "get_operation_research_problem_answer":
                user_question = arguments.get("user_question", "")
                model_name = arguments.get("model_name", DEFAULT_MODEL)
                max_attempts = arguments.get("max_attempts", 3)
                
                result = get_operation_research_problem_answer(user_question, model_name, max_attempts)
                return web.json_response({"jsonrpc": "2.0", "result": result, "id": data.get("id")})
            
            if tool_name == "health_check":
                result = health_check()
                return web.json_response({"jsonrpc": "2.0", "result": result, "id": data.get("id")})
            
            return web.json_response({"jsonrpc": "2.0", "error": {"code": -32601, "message": f"Method {tool_name} not found"}, "id": data.get("id")})
        
        return web.json_response({"jsonrpc": "2.0", "error": {"code": -32601, "message": f"Method {data.get('method')} not found"}, "id": data.get("id")})
    
    except Exception as e:
        logger.error(f"Error handling request: {str(e)}")
        return web.json_response({"jsonrpc": "2.0", "error": {"code": -32603, "message": f"Internal error: {str(e)}"}, "id": data.get("id", 0)})

# Basic GET handlers
async def handle_get(request):
    return web.Response(text=f"{SERVER_NAME} MCP Server is running. Use JSON-RPC for API calls.")

async def handle_health(request):
    result = health_check()
    return web.Response(text=result)

# Main function to run the server
def run_server():
    app = web.Application()
    app.router.add_get('/', handle_get)
    app.router.add_get('/health', handle_health)
    app.router.add_post('/', handle_jsonrpc)
    app.router.add_post('/tools/call', handle_jsonrpc)
    
    logger.info(f"🔧 Starting {SERVER_NAME} server...")
    logger.info(f"📡 Server will be available at: http://{HOST}:{PORT}")
    logger.info("🛠️  Available endpoints: /, /health, /tools/call")
    
    web.run_app(app, host=HOST, port=PORT, access_log=logger)

if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
