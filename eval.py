import openai
import anthropic
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import argparse
from src.modules.utils import (
    or_llm_agent,
    gpt_code_agent_simple,
    eval_model_result
)

# Load environment variables from .env file
load_dotenv()

# Anthropic API setup
anthropic_api_data = dict(
    api_key = os.getenv("CLAUDE_API_KEY"),
)
anthropic_client = anthropic.Anthropic(
    api_key=anthropic_api_data["api_key"]
)

# Ollama API setup
ollama_api_data = dict(
    base_url = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
)

# OpenAI API setup
openai_api_data = dict(
    api_key = os.getenv("OPENAI_API_KEY"),
    base_url = os.getenv("OPENAI_API_BASE")
)  
openai_client = openai.OpenAI(
    api_key=openai_api_data["api_key"],
    base_url=openai_api_data["base_url"] if openai_api_data["base_url"] else None
)

# Gemini API setup
gemini_api_data = dict(
    api_key = os.getenv("GEMINI_API_KEY"),
)
genai.configure(
    api_key=gemini_api_data["api_key"]
)

def parse_args():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: The parsed arguments
    """
    parser = argparse.ArgumentParser(description='Run optimization problem solving with LLMs')
    parser.add_argument('--agent', action='store_true', 
                        help='Use the agent. If not specified, directly use the model to solve the problem')
    parser.add_argument('--model', type=str, default='gpt-4',
                        help='Model name to use for LLM queries. Use "claude-..." for Claude models or "ollama:..." for Ollama models.')
    parser.add_argument('--data_path', type=str, default='data/datasets/dataset_combined_result.json',
                        help='Path to the dataset JSON file')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    with open(args.data_path, 'r') as f:
        dataset = json.load(f)
    #print(dataset['0'])

    model_name = args.model

    pass_count = 0
    correct_count = 0
    error_datas = []
    for i, d in dataset.items():
        print(f"=============== num {i} ==================")
        user_question, answer = d['question'], d['answer']
        print(user_question)
        print('-------------')
        
        if args.agent:
            is_solve_success, llm_result = or_llm_agent(user_question, model_name)
        else:
            is_solve_success, llm_result = gpt_code_agent_simple(user_question, model_name)
            
        if is_solve_success:
            print(f"Successfully executed code, optimal solution value: {llm_result}")
        else:
            print("Failed to execute code.")
        print('------------------')
        pass_flag, correct_flag = eval_model_result(is_solve_success, llm_result, answer)

        pass_count += 1 if pass_flag else 0
        correct_count += 1 if correct_flag else 0

        if not pass_flag or not correct_flag:
            error_datas.append(i)

        print(f'solve: {is_solve_success}, llm: {llm_result}, ground truth: {answer}')
        print(f'[Final] run pass: {pass_flag}, solve correct: {correct_flag}')
        print(' ')
            
    print(f'[Total {len(dataset)}] run pass: {pass_count}, solve correct: {correct_count}')
    print(f'[Total fails {len(error_datas)}] error datas: {error_datas}')
