import openai
import anthropic
import requests
import google.generativeai as genai
from dotenv import load_dotenv
import os
import re
import subprocess
import sys
import tempfile
import copy
from itertools import zip_longest

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


def is_number_string(s):
    """
    Determine if a string is a numeric string, including integers and decimals.

    Args:
    s: The string to be checked.

    Returns:
    True if the string is a numeric string, otherwise False.
    """
    pattern = r"^[-+]?\d+(\.\d+)?$"  # Regular expression to match integers or decimals
    return re.match(pattern, s) is not None

def convert_to_number(s):
    """
    Convert a string to a number (integer or float).

    Args:
        s: The string to be converted.

    Returns:
        int or float: Returns int if the string represents an integer, float if it represents a decimal.
        Returns None if conversion fails.
    """
    try:
        # Try to convert to integer
        if s.isdigit() or (s.startswith('-') and s[1:].isdigit()):
            return int(s)
        # Try to convert to float
        num = float(s)
        return num
    except (ValueError, TypeError):
        return None

def extract_best_objective(output_text):
    """
    Extract Best objective or Optimal objective value from Gurobi output.
    
    Args:
        output_text: Gurobi output text
    
    Returns:
        float or None: Optimal solution value, returns None if not found
    """
    # First check if model is infeasible
    if "Model is infeasible" in output_text:
        return None
    
    # Try to find Best objective
    match = re.search(r'Best objective\s+([\d.e+-]+)', output_text)
    if not match:
        # If not found, try to find Optimal objective
        match = re.search(r'Optimal objective\s+([\d.e+-]+)', output_text)
    
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    
    return None

def extract_and_execute_python_code(text_content):
    """
    Extract Python code blocks from text and execute them.

    Args:
        text_content: Text content containing code blocks.

    Returns:
        bool: True if execution was successful, False otherwise
        str: Error message if execution failed, best objective if successful
    """
    python_code_blocks = re.findall(r'```python\s*([\s\S]*?)```', text_content)

    if not python_code_blocks:
        print("No Python code blocks found.")
        return False, "No Python code blocks found"

    for code_block in python_code_blocks:
        code_block = code_block.strip()
        if not code_block:
            print("Found an empty Python code block, skipped.")
            continue

        print("Found Python code block, starting execution...")
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp_file:
                tmp_file.write(code_block)
                temp_file_path = tmp_file.name

            result = subprocess.run([sys.executable, temp_file_path], capture_output=True, text=True, check=False)

            if result.returncode == 0:
                print("Python code executed successfully, output:\n")
                print(result.stdout)
                
                best_obj = extract_best_objective(result.stdout)
                if best_obj is not None:
                    print(f"\nOptimal solution value (Best objective): {best_obj}")
                else:
                    print("\nOptimal solution value not found")
                return True, str(best_obj)
            else:
                print(f"Python code execution error, error message:\n")
                print(result.stderr)
                return False, result.stderr

        except Exception as e:
            print(f"Error occurred while executing Python code block: {e}")
            return False, str(e)
        finally:
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        print("-" * 30)

    return False, "No valid code blocks executed"

def eval_model_result(success, result, ground_truth, err_range=0.1):
    pass_flag = False
    correct_flag = False
    if success:
        pass_flag = True
        if is_number_string(str(result)) and ground_truth is not None:
            result_num = convert_to_number(str(result))
            ground_truth_num = convert_to_number(str(ground_truth))
            if abs(result_num - ground_truth_num) < err_range:
                correct_flag = True
        elif result == 'None': # no available solution
            if ground_truth is None or ground_truth == 'None':
                correct_flag = True
    return pass_flag, correct_flag 


def query_llm(messages, model_name="gpt-4", temperature=0.2):
    """
    Call LLM to get response results.
    
    Args:
        messages (list): List of conversation context.
        model_name (str): LLM model name, default is "gpt-4".
                         For Ollama models, prefix with "ollama:" (e.g., "ollama:llama2")
        temperature (float): Controls the randomness of output, default is 0.2.

    Returns:
        str: Response content generated by the LLM.
    """
    # Check if model is Ollama
    if model_name.lower().startswith("ollama:"):
        # Extract the actual model name after the "ollama:" prefix
        ollama_model = model_name.split(":", 1)[1]
        
        # Prepare the request payload
        payload = {
            "model": ollama_model,
            "messages": messages,
            "temperature": temperature,
            "stream": False
        }
        
        # Make the API request to Ollama
        response = requests.post(
            f"{ollama_api_data['base_url']}/api/chat",
            json=payload
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            return result["message"]["content"]
        else:
            error_msg = f"Ollama API error: {response.status_code} - {response.text}"
            print(error_msg)
            return f"Error: {error_msg}"
    
    # Check if model is Claude (Anthropic)
    elif model_name.lower().startswith("claude"):
        # Convert OpenAI message format to Anthropic format
        system_message = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_messages = [m["content"] for m in messages if m["role"] == "user"]
        assistant_messages = [m["content"] for m in messages if m["role"] == "assistant"]
        
        # Combine messages into a single conversation string
        conversation = system_message + "\n\n"
        for user_msg, asst_msg in zip_longest(user_messages, assistant_messages, fillvalue=None):
            if user_msg:
                conversation += f"Human: {user_msg}\n\n"
            if asst_msg:
                conversation += f"Assistant: {asst_msg}\n\n"
        
        # Add the final user message if there is one
        if len(user_messages) > len(assistant_messages):
            conversation += f"Human: {user_messages[-1]}\n\n"

        response = anthropic_client.messages.create(
            model=model_name,
            max_tokens=8192,
            temperature=temperature,
            messages=[{
                "role": "user",
                "content": conversation
            }]
        )
        return response.content[0].text
    
    # Check if model is gemini:
    elif model_name.lower().startswith('gemini'):
        gemini_messages = []
        gemini_client = genai.GenerativeModel(model_name)
        for message in messages:
            if message["role"] == "system":
                # Gemini doesn't have explicit system role, prepend to first user message
                continue
            elif message["role"] == "user":
                gemini_messages.append({
                    "role": "user",
                    "parts": [message["content"]]
                })
            elif message["role"] == "assistant":
                gemini_messages.append({
                    "role": "model",
                    "parts": [message["content"]]
                })
            
        # Add system message to the first user message if exists
        system_message = next((m["content"] for m in messages if m["role"] == "system"), "")
        if system_message:
            # Find the first user message and prepend system message to it
            for msg in gemini_messages:
                if msg["role"] == "user":
                    msg["parts"][0] = f"{system_message}\n\n{msg['parts'][0]}"
                    break
            else:
                # If no user message found, create one with just the system message
                gemini_messages.insert(0, {
                    "role": "user", 
                    "parts": [system_message]
                })
            
        # Generate response
        response = gemini_client.generate_content(
            gemini_messages,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=8192,
            )
        )  
        return response.text
            
    else:
        # Use OpenAI API
        response = openai_client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content

def generate_or_code_solver(messages_bak, model_name, max_attempts):
    messages = copy.deepcopy(messages_bak)

    gurobi_code = query_llm(messages, model_name)
    print("[Python Gurobi Code]:\n", gurobi_code)

    # 4. Code execution & fixes
    text = f"{gurobi_code}"
    attempt = 0
    while attempt < max_attempts:
        success, error_msg = extract_and_execute_python_code(text)
        if success:
            messages_bak.append({"role": "assistant", "content": gurobi_code})
            return True, error_msg, messages_bak

        print(f"\nAttempt {attempt + 1} failed, requesting LLM to fix code...\n")

        # Build repair request
        messages.append({"role": "assistant", "content": gurobi_code})
        messages.append({"role": "user", "content": f"Code execution encountered an error, error message is as follows:\n{error_msg}\nPlease fix the code and provide the complete executable code again."})

        # Get the fixed code
        gurobi_code = query_llm(messages, model_name)
        text = f"{gurobi_code}"

        print("\nReceived fixed code, preparing to execute again...\n")
        attempt += 1
    # not add gurobi code
    messages_bak.append({"role": "assistant", "content": gurobi_code})
    print(f"Reached maximum number of attempts ({max_attempts}), could not execute code successfully.")
    return False, None, messages_bak

def or_llm_agent(user_question, model_name="gpt-4", max_attempts=3):
    """
    Request Gurobi code solution from LLM and execute it, attempt to fix if it fails.

    Args:
        user_question (str): User's problem description.
        model_name (str): LLM model name to use, default is "gpt-4".
        max_attempts (int): Maximum number of attempts, default is 3.

    Returns:
        tuple: (success: bool, best_objective: float or None, final_code: str)
    """
    # Initialize conversation history
    messages = [
        {
            "role": "system",
            "content": (
                "You are an operations research expert. Based on the optimization problem "
                "provided by the user, construct a mathematical model that effectively "
                "models the original problem using mathematical (linear programming) expressions.\n\n"
                "Follow these steps:\n"
                "1. Identify the decision variables and clearly define what each variable represents\n"
                "2. Formulate the objective function (min or max)\n"
                "3. List all constraints with clear mathematical expressions\n"
                "4. Specify any bounds or restrictions on variables\n\n"
                "Focus on obtaining a correct mathematical model expression without too "
                "much concern for explanations. This model will be used later to guide "
                "the generation of Gurobi code, and this step is mainly used to generate "
                "effective linear scale expressions."
            )
        },
        {
            "role": "user",
            "content": user_question
        }
    ]

    # 1. Generate mathematical model - MATH MODEL
    math_model = query_llm(messages, model_name)
    print("[Mathematical Model]:\n", math_model)

    
    # 2. Validate mathematical model - MATH MODEL
    messages.append(
        {
        "role": "assistant",
        "content": math_model
        }
    )

    messages.append(
        {
            "role": "user",
            "content": (
                "Please verify whether the above mathematical model correctly and completely "
                "represents the original problem stated earlier in natural language.\n\n"
                "Specifically:\n"
                "1. **Check correctness** of the objective function, constraints, variables, and sets.\n"
                "2. **Identify and fix any errors, omissions, or misinterpretations** from the original problem.\n"
                "3. If the model is already correct, check if it can be **simplified or written more concisely**.\n"
                "4. Finally, output the **corrected or optimized mathematical model** in full.\n\n"
                "Be precise, and think like a mathematical model auditor or a reviewer."
            )
        }
    )


    validate_math_model = query_llm(messages, model_name)
    print("[Validated Mathematical Model]:\n", validate_math_model)
    

    # 3. Generating Python code + fixing using Gurobi - CODE GENERATION
    messages.append(
        {
            "role": "assistant",
            "content": validate_math_model
        }
    )

    messages.append(
        {
            "role": "user",
            "content": (
                "Based on the above mathematical model, write complete and reliable Python code using Gurobi to solve "
                "this operations research optimization problem.\n\n"
                "Your code must follow this structure:\n"
                "1. Import necessary libraries (gurobipy, numpy, etc.)\n"
                "2. Create a model instance\n"
                "3. Define and add variables with appropriate bounds\n"
                "4. Set the objective function\n"
                "5. Add all constraints\n"
                "6. Optimize the model\n"
                "7. Extract and print the results, including the optimal objective value\n"
                "8. Handle potential infeasibility or unboundedness\n\n"
                "Output in the format ```python\n{code}\n```, without code explanations."
            )
        }
    )

    # Copy msg; solve; add the laset gurobi code 
    is_solve_success, result, messages = generate_or_code_solver(messages, model_name, max_attempts)
    print(f"[Stage result: {is_solve_success}, {result}]")

    # Check if solve successfully
    if is_solve_success:
        if not is_number_string(result):
            print('!![No available solution warning]!!')

            # No solution
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "The current model resulted in *no feasible solution*. This indicates one of these issues:\n"
                        "1. Contradictory constraints making the problem infeasible\n"
                        "2. Incorrect variable bounds\n"
                        "3. Errors in constraint formulation\n\n"
                        "Please carefully analyze the mathematical model and Gurobi code. Add diagnostic code to identify "
                        "which constraints are causing infeasibility. Then fix the issues and provide the complete corrected code.\n\n"
                        "Output in the format ```python\n{code}\n```, without code explanations."
                    )
                }
            )
            is_solve_success, result, messages = generate_or_code_solver(messages, model_name, max_attempts=1)
        else:
            print('!![Max attempt debug error warning]!!')

            messages.append(
                {
                    "role": "user",
                    "content": (
                        "The model code still reports errors after multiple debugging attempts. Here are common issues to address:\n"
                        "1. Check for syntax errors or undefined variables\n"
                        "2. Ensure all constraints use proper Gurobi syntax (e.g., model.addConstr() not just expressions)\n"
                        "3. Verify that all mathematical operations are valid (e.g., no division by zero)\n"
                        "4. Confirm that variable types match their usage (continuous vs. integer vs. binary)\n\n"
                        "Please completely rebuild the Gurobi Python code with careful attention to these details.\n"
                        "Output in the format ```python\n{code}\n```, without code explanations."
                    )
                }
            )
            is_solve_success, result, messages = generate_or_code_solver(messages, model_name, max_attempts=2)

    return is_solve_success, result
def gpt_code_agent_simple(user_question, model_name="gpt-4", max_attempts=3):
    """
    Request Gurobi code solution from LLM and execute it, attempt to fix if it fails.

    Args:
        user_question (str): User's problem description.
        model_name (str): LLM model name to use, default is "gpt-4".
        max_attempts (int): Maximum number of attempts, default is 3.

    Returns:
        tuple: (success: bool, best_objective: float or None, final_code: str)
    """
    # Initialize conversation history
    messages = [
        {
            "role": "system", 
            "content": (
                "You are an operations research expert. Based on the optimization problem provided by the user, construct a mathematical "
                "model and write complete, reliable Python code using Gurobi to solve the operations research optimization problem."
                "The code should include necessary model construction, variable definitions, constraint additions, objective function "
                "settings, as well as solving and result output."
                "Output in the format ```python\n{code}\n```, without code explanations."
            )
        },
        {
            "role": "user",
            "content": user_question
        }
    ]

    # copy msg; solve; add the laset gurobi code
    gurobi_code = query_llm(messages, model_name)
    print("[Python Gurobi Code]:\n", gurobi_code)
    text = f"{gurobi_code}"
    is_solve_success, result = extract_and_execute_python_code(text)
    
    print(f'Stage result: {is_solve_success}, {result}')
    
    return is_solve_success, result