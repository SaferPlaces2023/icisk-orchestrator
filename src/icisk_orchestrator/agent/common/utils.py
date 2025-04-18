# DOC: Generic utils

import os
import sys
import re
import ast
import uuid
import tempfile

from typing import Sequence

from langchain_openai import ChatOpenAI

from langchain_core.messages import RemoveMessage, AIMessage




# REGION: [Generic utils]

_temp_dir = os.path.join(tempfile.gettempdir(), 'icisk-chat')
os.makedirs(_temp_dir, exist_ok=True)


def guid():
    return str(uuid.uuid4())


def python_path():
    """ python_path - returns the path to the Python executable """
    pathname, _ = os.path.split(normpath(sys.executable))
    return pathname


def normpath(pathname):
    """ normpath - normalizes the path to use forward slashes """
    if not pathname:
        return ""
    return os.path.normpath(pathname.replace("\\", "/")).replace("\\", "/")


def juststem(pathname):
    """ juststem - returns the file name without the extension """
    pathname = os.path.basename(pathname)
    root, _ = os.path.splitext(pathname)
    return root


def justpath(pathname, n=1):
    """ justpath - returns the path without the last n components """
    for _ in range(n):
        pathname, _ = os.path.split(normpath(pathname))
    if pathname == "":
        return "."
    return normpath(pathname)


def justfname(pathname):
    """ justfname - returns the basename """
    return normpath(os.path.basename(normpath(pathname)))


def justext(pathname):
    """ justext - returns the file extension without the dot """
    pathname = os.path.basename(normpath(pathname))
    _, ext = os.path.splitext(pathname)
    return ext.lstrip(".")

def forceext(pathname, newext):
    """ forceext - replaces the file extension with newext """
    root, _ = os.path.splitext(normpath(pathname))
    pathname = root + ("." + newext if len(newext.strip()) > 0 else "")
    return normpath(pathname)

def try_default(f, default_value=None):
    """ try_default - returns the value if it is not None, otherwise returns default_value """
    try:
        value = f()
        return value
    except Exception as e:
        return default_value
    
    
def safe_code_lines(code, format_dict=None):
    if format_dict is not None:
        code = code.format(**format_dict)
    lines = code.split('\n')
    if len(lines) > 0:
        while lines[0] == '':
            lines = lines[1:]
        while lines[-1] == '':
            lines = lines[:-1]
        spaces = re.match(r'^\s*', lines[0])
        spaces = len(spaces.group()) if spaces else 0
        lines = [line[spaces:] for line in lines]
        lines = [f'{line}\n' if idx!=len(lines)-1 else f'{line}' for idx,line in enumerate(lines)]
    code = ''.join(lines)
    return code
    

# ENDREGION: [Generic utils]



# REGION: [LLM and Tools]

_base_llm = ChatOpenAI(model="gpt-4o-mini")

def ask_llm(role, message, llm=_base_llm, eval_output=False):
    llm_out = llm.invoke([{"role": role, "content": message}])
    if eval_output:
        try: 
            content = llm_out.content
            if type(content) is str and content.startswith('```python'):
                content = content.split('```python')[1].split('```')[0]
            return ast.literal_eval(content)
        except: 
            pass
    return llm_out.content

# ENDREGION: [LLM and Tools]



# REGION: [Message utils funtion]

def merge_sequences(left: Sequence[str], right: Sequence[str]) -> Sequence[str]:
    """Add two lists together."""
    return left + right

def is_ai_message(message):
    return message.type == 'ai'

def is_system_message(message):
    return message.type == 'system'

def is_human_message(message):
    return message.type == 'human'

def last_human_message(state):
    if 'messages' in state and len(state['messages']) > 0:
        recent_messages = state['messages'][::-1]
        for message in recent_messages:
            if is_human_message(message):
                return message
    return None

def remove_message(message_id):
    return RemoveMessage(id = message_id)

def remove_tool_messages(tool_messages):
    if type(tool_messages) is not list:
        return remove_message(tool_messages.id)
    else:
        return [remove_message(tm.id) for tm in tool_messages]
    
def build_tool_message(message_id, tool_name, tool_args):
    tool_message = AIMessage(
        content = '',
        tool_calls = [
            {
                "id": message_id,
                "name": tool_name,
                "args": { arg_name: arg_value for arg_name, arg_value in tool_args.items() }
            }
        ]
    )
    return tool_message
    
def tool_response_message(tool_call_id, tool_name, tool_result):
    message = {
        "role": "tool",
        "name": tool_name,
        "content": tool_result,
        "tool_call_id": tool_call_id,
    }
    return message
    
# ENDREGION: [Message utils funtion]
    