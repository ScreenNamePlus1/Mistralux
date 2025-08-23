#!/usr/bin/env python3
# aishell.py
# A Python-based command-line shell with AI-powered features using Mistral AI, Hugging Face APIs, or local inference.

import subprocess
import os
import sys
import requests
from cmd import Cmd
import shlex
from functools import lru_cache
from termcolor import colored
import readline
import glob
import time
import re  # Added for ANSI code stripping
try:
    from transformers import pipeline
    import torch
except ImportError:
    pipeline = None
    torch = None

class AIShell(Cmd):
    intro = colored("Welcome to AI Shell with Mistral/Hugging Face/Local integration. Type help or ? for assistance.\n", "green")

    def __init__(self):
        super().__init__()
        self.mistral_api_key = os.getenv("MISTRAL_API_KEY")
        self.huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.ai_provider = "mistral"  # Default: mistral, huggingface, or local
        self.use_ai = True
        self.mistral_model = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
        self.huggingface_model = os.getenv("HUGGINGFACE_MODEL", "mistralai/Mixtral-8x7B-Instruct-v0.1")
        self.local_model = None
        self.aliases = {}
        self.plain_prompt = ""  # Store plain-text prompt
        if not self.mistral_api_key and not self.huggingface_api_key and not pipeline:
            print(colored("Error: No API keys or transformers library available.", "red"))
            sys.exit(1)
        if pipeline and not (self.mistral_api_key or self.huggingface_api_key):
            print(colored("No API keys found. Initializing local model...", "yellow"))
            try:
                self.local_model = pipeline("text-generation", model="mistralai/Mistral-7B-Instruct-v0.2",
                                           device=-1, load_in_4bit=True)
                self.ai_provider = "local"
            except Exception as e:
                print(colored(f"Failed to load local model: {e}", "red"))
                sys.exit(1)
        history_file = os.path.expanduser("~/.aishell_history")
        try:
            readline.read_history_file(history_file)
        except FileNotFoundError:
            pass
        readline.set_history_length(1000)
        import atexit
        atexit.register(readline.write_history_file, history_file)
        self.update_prompt()

    def update_prompt(self):
        venv = os.getenv("VIRTUAL_ENV")
        venv_name = os.path.basename(venv) if venv else ""
        cwd = os.path.basename(os.getcwd())
        provider = self.ai_provider.capitalize()
        # Plain-text prompt for readline and cmd
        self.plain_prompt = f"[{provider}]{venv_name}:{cwd} $ " if venv else f"[{provider}]{cwd} $ "
        # Colored prompt for display
        self.prompt = colored(self.plain_prompt, "blue")

    # NEW METHODS ADDED BELOW
    def strip_ansi_codes(self, text):
        """Remove ANSI escape codes from text."""
        ansi_regex = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_regex.sub('', text)

    def preloop(self):
        """Set up the prompt before entering the command loop."""
        # Ensure readline uses the plain prompt to avoid length miscalculations
        readline.set_completer_delims(readline.get_completer_delims())
        readline.set_prompt(self.strip_ansi_codes(self.prompt))

    def postcmd(self, stop, line):
        """Ensure the prompt is redisplayed correctly after each command."""
        print()  # Add a newline to prevent overwriting
        self.update_prompt()  # Update prompt in case directory or provider changes
        return stop
    # END OF NEW METHODS

    @lru_cache(maxsize=100)
    def query_mistral(self, prompt, model=None):
        # ... (unchanged, same as your script)
        # ... (omitted for brevity, but keep your existing implementation)
        pass  # Replace with your original query_mistral method

    def query_huggingface(self, prompt, model=None):
        # ... (unchanged, same as your script)
        pass  # Replace with your original query_huggingface method

    def is_safe_command(self, command):
        # ... (unchanged, same as your script)
        pass  # Replace with your original is_safe_command method

    def default(self, line):
        # ... (unchanged, same as your script)
        pass  # Replace with your original default method

    def suggest_fix(self, original_command, error):
        # ... (unchanged, same as your script)
        pass  # Replace with your original suggest_fix method

    def do_natural(self, line):
        # ... (unchanged, same as your script)
        pass  # Replace with your original do_natural method

    def do_explain(self, line):
        # ... (unchanged, same as your script)
        pass  # Replace with your original do_explain method

    def do_generate_script(self, line):
        # ... (unchanged, same as your script)
        pass  # Replace with your original do_generate_script method

    def do_summarize(self, line):
        # ... (unchanged, same as your script)
        pass  # Replace with your original do_summarize method

    def do_switch_ai(self, arg):
        # ... (unchanged, same as your script)
        pass  # Replace with your original do_switch_ai method

    def do_toggle_ai(self, arg):
        # ... (unchanged, same as your script)
        pass  # Replace with your original do_toggle_ai method

    def do_alias(self, line):
        # ... (unchanged, same as your script)
        pass  # Replace with your original do_alias method

    def do_cd(self, path):
        # ... (unchanged, same as your script)
        pass  # Replace with your original do_cd method

    def do_pwd(self, arg):
        # ... (unchanged, same as your script)
        pass  # Replace with your original do_pwd method

    def do_exit(self, arg):
        # ... (unchanged, same as your script)
        pass  # Replace with your original do_exit method

    def do_help(self, arg):
        # ... (unchanged, same as your script)
        pass  # Replace with your original do_help method

    def complete_natural(self, text, line,