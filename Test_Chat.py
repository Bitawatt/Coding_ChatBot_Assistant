#!/home/bitawatt/anaconda3/envs/Code_Chat-env/bin/python
import argparse
import json
import os
import textwrap
import time
from datetime import datetime
from typing import Any, Union
from typing import List

from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import TerminalFormatter

import openai

class AppState:
    def __init__(self):
        self.MODEL_NAME = "gpt-4"
        self.MODEL_TEMPERATURE = 0.1
        self.MODEL_MAX_TOKENS = 7500
        self.ALL_MESSAGES = list()

# ANSI escape codes for text colors
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
MAGENTA = '\033[35m'
CYAN = '\033[36m'
RESET = '\033[0m'

app_state = AppState()


# Section:    logging for debug functions

def create_log_file(suffix: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = "log/openai"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = os.path.join(log_dir, f"{timestamp}{suffix}")
    return log_file


def save_request_as_human_readable_text(conversation, suffix):
    log_file = create_log_file(suffix)
    human_readable_text = ""
    for message in conversation:
        if 'role' in message and 'content' in message:
            human_readable_text += f"# {message['role'].upper()}:\n{message['content']}\n\n"
        else:
            print(f"{BLUE}Skipping message due to missing 'role' or 'content': {message}{RESET}")
    save_content_to_file(log_file, human_readable_text)


def save_response_as_human_readable_text(response, total_tokens, duration, suffix=""):
    log_file = create_log_file(suffix)
    conversation: List[dict] = response["choices"]
    human_readable_text = f"- Model      : {app_state.MODEL_NAME}\n"
    human_readable_text += f"- Temperature: {app_state.MODEL_TEMPERATURE}\n"
    human_readable_text += f"- Tokens     : {total_tokens}\n"
    human_readable_text += f"- Duration   : {duration}\n"
    human_readable_text += "\n\n"
    for message in conversation:
        message = message["message"]
        if 'role' in message and 'content' in message:
            human_readable_text += f"# {message['role'].upper()}:\n{message['content']}\n\n"
        else:
            print(f"{BLUE}Skipping message due to missing 'role' or 'content': {message}{RESET}")
    save_content_to_file(log_file, human_readable_text)


def pretty_print_json(conversation: Any) -> Union[str, Any]:
    try:
        return json.dumps(conversation, indent=4, sort_keys=True)
    except Exception:
        return conversation


def save_json_log(conversation, suffix, pretty_print=True):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = "log/openai"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = os.path.join(log_dir, f"{timestamp}{suffix}.json")
    if pretty_print:
        conversation = pretty_print_json(conversation)
    save_content_to_file(log_file, str(conversation))


# Section:     file operations

def save_content_to_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)


def read_file_content(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
        return infile.read()


# Section:     API functions

def fetch_chatbot_response(conversation: List[dict]) -> dict:
    return openai.ChatCompletion.create(
        model=app_state.MODEL_NAME,
        messages=conversation,
        temperature=app_state.MODEL_TEMPERATURE,
        # max_tokens=app_state.MODEL_MAX_TOKENS,
    )


def handle_error(error, conversation):
    print(f'{RED}\n\nError communicating with OpenAI: "{error}"{RESET}')
    if 'maximum context length' in str(error):
        conversation.pop(0)
        print('\n\n DEBUG: Trimming oldest message')
        return True, conversation
    return False, conversation


def perform_chatbot_conversation(conversation: List[dict]) -> tuple[Any, Any, float]:
    max_retry: int = 7

    # Save the conversation to a log file
    save_json_log(conversation, f'_{app_state.MODEL_NAME}_request')
    save_request_as_human_readable_text(conversation, f"_{app_state.MODEL_NAME}_request.md")

    for retry in range(max_retry):
        try:
            start_time = time.time()
            print(f"{YELLOW}INFO: Processing...{RESET}")

            response = fetch_chatbot_response(conversation)
            text = response['choices'][0]['message']['content']
            total_tokens = response['usage']['total_tokens']

            # Check if the text is bookended with '''
            if text.startswith("```") and text.endswith("```"):
            # Remove the bookends and highlight the code
                code = text[3:-3]
                highlighted_code = highlight(code, PythonLexer(), TerminalFormatter())
                text = highlighted_code
                
            end_time = time.time()
            processing_time = end_time - start_time

            save_json_log(response, f'_{total_tokens}_response', False)
            save_response_as_human_readable_text(
                response, total_tokens, processing_time,
                f"_{total_tokens}_response.md",
            )

            return text, total_tokens, processing_time
        except Exception as oops:
            should_continue, conversation = handle_error(oops, conversation)
            if not should_continue:
                wait_time = 2 ** retry * 5
                print(f'\n\nRetrying in {wait_time} seconds...')
                time.sleep(wait_time)
            else:
                continue

    print(f"{RED}\n\nExiting due to excessive errors in API.{RESET}")
    exit(1)


###     MAIN LOOP


def multi_line_input():
    print(f'{CYAN}\n\n\nType END to save and exit.\n{YELLOW}[MULTI] USER:\n{RESET}')
    lines = []
    while True:
        line = input()
        if line == "END":
            break
        lines.append(line)
    return "\n".join(lines)


def get_user_input():
    # get user input
    try:
        text = input(f'{GREEN}[{app_state.MODEL_NAME}] USER PROMPT: {RESET}')
    except KeyboardInterrupt:
        text = '^C'
    if 'END' == text or '^C' in text:
        print(f'{BLUE}\n\nExiting...{RESET}')
        exit(0)
    if 'SCRATCHPAD' == text or 'M' == text:
        text = multi_line_input()
        save_content_to_file('scratchpad.md', text.strip('END').strip())
        print(f'{CYAN}\n\n#####      Scratchpad updated!{RESET}')
        return None
    return text

def print_chatbot_response(response, total_tokens, processing_time):
    print(f'{BLUE}\n\n\n\nCHATBOT response:\n{RESET}')
    if '```' in response:
        start_index = response.find('\n```') + 1
        end_index = response.find('\n```', start_index) + 4
        if end_index != -1:
            code = response[start_index:end_index]
            highlighted_code = highlight(code, PythonLexer(), TerminalFormatter())
            print(highlighted_code)
        else:
            formatted_lines = [textwrap.fill(line, width=120) for line in response.split('\n')]
            formatted_text = '\n'.join(formatted_lines)
            print(formatted_text)
    else:
        formatted_lines = [textwrap.fill(line, width=120) for line in response.split('\n')]
        formatted_text = '\n'.join(formatted_lines)
        print(formatted_text)
    print(f'{MAGENTA}\n\nINFO: {app_state.MODEL_NAME}: {total_tokens} tokens, {processing_time:.2f} seconds{RESET}')
    
def main():
    # instantiate chatbot
    openai.api_key = read_file_content('key_openai.txt').strip()

    # parse arguments
    parser = argparse.ArgumentParser(description="Chatbot using OpenAI API")
    parser.add_argument("--model", default=app_state.MODEL_NAME,
                        help="Model name (default: %(default)s)")
    parser.add_argument("--temperature", type=float, default=app_state.MODEL_TEMPERATURE,
                        help="Temperature (default: %(default)s)")
    args, unknown = parser.parse_known_args()

    app_state.MODEL_NAME = args.model
    app_state.MODEL_TEMPERATURE = args.temperature

    print(f"Current settings:\n"
        f"Model: {app_state.MODEL_NAME}\n"
        f"Temperature: {app_state.MODEL_TEMPERATURE}")
    print("Sample app usage: python chat.py --model gpt-3.5-turbo --temperature 0.2")


    print(f"{MAGENTA}\n\n****** IMPORTANT ******\n"
        "Type 'SCRATCHPAD' or 'M' to enter multi-line input mode to update the scratchpad.\n"
        f"Type 'END' to save and exit.\n{RESET}")

    while True:
        text = get_user_input()
        if text is None:
            continue
        if text == '':
            # empty submission, probably on accident
            continue

        # continue with composing conversation and response
        app_state.ALL_MESSAGES.append({'role': 'user', 'content': text})
        system_message = read_file_content('system_message.txt').replace('<<CODE>>', read_file_content('scratchpad.md'))
        conversation = list()
        conversation += app_state.ALL_MESSAGES
        conversation.append({'role': 'system', 'content': system_message})

        # generate a response
        response, tokens, processing_time = perform_chatbot_conversation(conversation)

        if tokens > app_state.MODEL_MAX_TOKENS:
            app_state.ALL_MESSAGES.pop(0)

        app_state.ALL_MESSAGES.append({'role': 'assistant', 'content': response})
        print_chatbot_response(response, tokens, processing_time)


if __name__ == '__main__':
    main()
