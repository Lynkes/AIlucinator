import os
import ollama
from langchain_community.llms import Ollama as ChainOllama
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
import textwrap
import re
import os
import subprocess
import sys
import shutil


# Initialize LangChain with Ollama
llm = ChainOllama(model="llama3")


# Get Tools List
def get_tools_list(folder_path):
    tools = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.py'):
            with open(os.path.join(folder_path, file_name), 'r') as file:
                description = extract_description(file)
                tools.append({
                    'name': file_name,
                    'description': description
                })
    return tools

def extract_description(file):
    description = ""
    for line in file:
        if line.startswith('#'):
            description += line.strip('#').strip() + ' '
        else:
            break
    return description.strip()

# Parse Tool Usage
# Add a requirements get to parse
def parse_tool_usage(response):
    lines = response.split('\n')
    tool_name = None
    usage_instructions = []

    for line in lines:
        if line.startswith('Use tool:'):
            tool_name = line.split('Use tool:')[-1].strip()
        elif line.startswith('Instructions:'):
            usage_instructions.append(line.split('Instructions:')[-1].strip())
        elif tool_name and line.strip():
            usage_instructions.append(line.strip())
    
    usage_instructions = " ".join(usage_instructions).strip()
    if tool_name != '':
        print("Got tool_name:",tool_name)
        print("Got usage_instructions:",usage_instructions)
        return tool_name, usage_instructions
    
def Task_Code_parse(code):
    lines = code.split('\n')
    Task_Code = None
    for line in lines:
        if line.startswith('# Task_Code:'):
            Task_Code = line.split('# Task_Code:')[-1].strip()
    if Task_Code != '':
        print("Got Task_Code:",Task_Code)
        return Task_Code
    else:
        print("Erro No Task_Code in code")
        return None
    

def comment_and_extract_code(text):
    # Define the regex pattern to match code blocks enclosed in triple backticks
    pattern = r'```(.*?)```'
    
    # Split the text by the pattern
    parts = re.split(pattern, text, flags=re.DOTALL)
    
    result = []
    
    for i, part in enumerate(parts):
        if i % 2 == 0:  # This is outside the code blocks
            commented_part = "\n".join(f"# {line}" for line in part.strip().split('\n'))
            result.append(commented_part)
        else:  # This is inside the code blocks
            result.append(part.strip())
    
    return "\n".join(result)
        


# Decide and Execute
def decide_and_execute(tools_list, task):
    response = chain.invoke({'tools_list': tools_list, 'task': task})
    if "write new code" in response.lower().strip():
        print("\nwriting new code!")
        code = generate_code(task)  # Use Ollama or another model to generate the code
        task_name = Task_Code_parse(code)
        if task_name != "":
            save_new_code(code, folder_path, task_name)  # Make sure to provide correct path
    else:
        print("\nparsing the Response:",response)
        tool_name, usage_instructions, requirements = parse_tool_usage(response)
        #execute_tool(tool_name, usage_instructions)
        execute_code(tool_name= tool_name, directory= folder_path, requirements_file=requirements)

def generate_code(task):
    code_generation_template = PromptTemplate(
        input_variables=["task"],
        template="""
        in the fist line write '# Task_Code:' followd by a name for the python script in the same line
        For writing new Python code, please include:
        1. A description of the approach commented by '#' in the second line.
        2. The function definition.
        3. Example usage of the function.
        
        Ensure the generated code is well-documented and follows best practices.
        Here is the task: {task}
        """
    )
    formatted_prompt = code_generation_template.format(task=task)
    message = ''
    stream = ollama.chat(model="llama3", messages=[{"role": "user", "content": formatted_prompt}], stream=True)
    print("\nOllama:")
    for chunk in stream:
        message += chunk['message']['content']
        print(chunk['message']['content'], end='', flush=True)
    print("\n")
    
    # Use textwrap to format the generated code
    formatted_code = textwrap.dedent(message).strip()
    return formatted_code

def save_new_code(code, folder_path, task_name):
    # Define the new directory path
    comment_and_extract_code(code)
    new_folder_path = os.path.join(folder_path, task_name)
    # Create the new directory if it doesn't exist
    os.makedirs(new_folder_path, exist_ok=True)
    # Write the code to the new file
    with open(new_folder_path +"/"+ task_name+".py", 'w') as file:
        file.write(code)


def execute_code(tool_name, directory, requirements_file=None):
    """
    Creates a virtual environment, installs requirements, executes the code,
    and captures any output or errors.

    Args:
        code (str): The Python code to execute.
        directory (str): The directory where the virtual environment will be created.
        requirements_file (str, optional): Path to the requirements.txt file.

    Returns:
        dict: A dictionary with 'stdout' and 'stderr' from the code execution.
    """
    # Paths
    venv_path = os.path.join(directory, 'venv')
    script_path = os.path.join(directory, tool_name, tool_name,'.py')

    # Create virtual environment
    if not os.path.exists(venv_path):
        subprocess.check_call([sys.executable, '-m', 'venv', venv_path])

    # Install requirements if provided
    if requirements_file and os.path.exists(directory, tool_name,'requirements.txt'):
        pip_executable = os.path.join(venv_path, 'Scripts', 'pip') if os.name == 'nt' else os.path.join(venv_path, 'bin', 'pip')
        subprocess.check_call([pip_executable, 'install', '-r', requirements_file])

    # # Write the code to a script file
    # with open(script_path, 'w') as file:
    #     file.write(tool_name)

    # Execute the script and capture output
    pip_executable = os.path.join(venv_path, 'Scripts', 'python') if os.name == 'nt' else os.path.join(venv_path, 'bin', 'python')
    
    try:
        result = subprocess.run([pip_executable, script_path], capture_output=True, text=True, check=True)
        return {'stdout': result.stdout, 'stderr': result.stderr}
    except subprocess.CalledProcessError as e:
        return {'stdout': e.stdout, 'stderr': e.stderr}

if __name__ == "__main__":
    # Example Usage
    folder_path = 'Allucinator/resources/Agent/.Playground'
    tools = get_tools_list(folder_path)
    tools_list = "\n".join([f"{tool['name']}: {tool['description']}" for tool in tools])
    task = "Create a function to sort a list of integers in ascending order."

    prompt_template = PromptTemplate(
    input_variables=["tools_list", "task"],
    template="""
    You can use Python to solve the task at hand. you can only use scripts that are on the list of available tools (Python scripts) in the folder with their descriptions you need to use the tools in the list like name.py or make them if they dont exist:
    available tools: {tools_list}
    
    Task: {task}
    
    If the script already exists and you think a listed tool can be used to achieve the task, please specify which tool by writing 'Use tool:' on a newline followed by the tool name and how to use it.
    Else If none of the tools fit the task requirements, please write 'write new code:' to accomplish the task.
    Here is what the parser will try to do.
    [
    for line in lines:
        if line.startswith('Use tool:'):
            tool_name = line.split('Use tool:')[-1].strip()
        elif line.startswith('Instructions:'):
            usage_instructions.append(line.split('Instructions:')[-1].strip())
        elif tool_name and line.strip():
            usage_instructions.append(line.strip())
    
    usage_instructions = " ".join(usage_instructions).strip()
    return tool_name, usage_instructions
    ]
    """
)
    chain = RunnableSequence(prompt_template | llm)

    decide_and_execute(tools_list, task)
