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
try:
    from termcolor import colored
    print("Debug: termcolor imported successfully")
except ImportError:
    print("Debug: termcolor not installed, defining fallback")
    def colored(text, *args, **kwargs):
        return text
import readline
import glob
import time
import re
print("Debug: Imports completed")

try:
    from transformers import pipeline
    import torch
    print("Debug: transformers and torch imported successfully")
except ImportError:
    pipeline = None
    torch = None
    print("Debug: transformers or torch not installed")

class AIShell(Cmd):
    intro = colored("Welcome to AI Shell with Mistral/Hugging Face/Local integration. Type help or ? for assistance.\n", "green")

    def __init__(self):
        print("Debug: Entering AIShell.__init__")
        super().__init__()
        self.mistral_api_key = os.getenv("MISTRAL_API_KEY")
        self.huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")
        print(f"Debug: MISTRAL_API_KEY: {'set' if self.mistral_api_key else 'not set'}")
        print(f"Debug: HUGGINGFACE_API_KEY: {'set' if self.huggingface_api_key else 'not set'}")
        self.ai_provider = "mistral"
        self.use_ai = True
        self.mistral_model = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
        self.huggingface_model = os.getenv("HUGGINGFACE_MODEL", "mistralai/Mixtral-8x7B-Instruct-v0.1")
        self.local_model = None
        self.aliases = {}
        self.plain_prompt = ""
        # Temporarily bypass API check to prevent silent exit
        # if not self.mistral_api_key and not self.huggingface_api_key and not pipeline:
        #     print(colored("Error: No API keys or transformers library available.", "red"))
        #     sys.exit(1)
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
        print("Debug: Calling update_prompt")
        self.update_prompt()
        print("Debug: AIShell.__init__ completed")

    def update_prompt(self):
        venv = os.getenv("VIRTUAL_ENV")
        venv_name = os.path.basename(venv) if venv else ""
        cwd = os.path.basename(os.getcwd())
        provider = self.ai_provider.capitalize()
        self.plain_prompt = f"[{provider}]{venv_name}:{cwd} $ " if venv else f"[{provider}]{cwd} $ "
        self.prompt = colored(self.plain_prompt, "blue")
        print(f"Debug: Updated prompt to '{self.prompt}'")

    def strip_ansi_codes(self, text):
        """Remove ANSI escape codes from text."""
        ansi_regex = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_regex.sub('', text)

    def preloop(self):
        """Set up the command loop."""
        readline.set_completer_delims(readline.get_completer_delims())
        self.update_prompt()
        print("Debug: Entering command loop")

    def postcmd(self, stop, line):
        """Ensure the prompt is redisplayed correctly after each command."""
        print("Debug: Postcmd called, adding newline")
        print()
        self.update_prompt()
        return stop

    @lru_cache(maxsize=100)
    def query_mistral(self, prompt, model=None):
        if self.ai_provider == "local" and self.local_model:
            print(colored("Querying local model...", "yellow"), end="", flush=True)
            try:
                result = self.local_model(prompt, max_length=200, temperature=0.2)[0]["generated_text"]
                print(colored("Done.", "green"))
                return result.strip()
            except Exception as e:
                print(colored(f"Local Model Error: {e}", "red"))
                return None
        elif self.ai_provider == "huggingface":
            return self.query_huggingface(prompt, model or self.huggingface_model)
        
        model = model or self.mistral_model
        url = ("https://codestral.mistral.ai/v1/chat/completions" if "codestral" in model.lower()
               else "https://api.mistral.ai/v1/chat/completions")
        headers = {"Authorization": f"Bearer {self.mistral_api_key}", "Content-Type": "application/json"}
        data = {"model": model, "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200, "temperature": 0.2}
        
        for attempt in range(3):
            print(colored("Querying Mistral AI...", "yellow"), end="", flush=True)
            try:
                response = requests.post(url, json=data, headers=headers)
                response.raise_for_status()
                print(colored("Done.", "green"))
                return response.json()["choices"][0]["message"]["content"].strip()
            except requests.exceptions.HTTPError as err:
                print(colored("Failed.", "red"))
                if err.response.status_code == 429:
                    print(colored("Mistral AI Error: Rate limit exceeded. Retrying...", "yellow"))
                    time.sleep(2 ** attempt)
                    continue
                elif err.response.status_code == 401:
                    print(colored("Mistral AI Error: 🚫 Authentication failed. Check MISTRAL_API_KEY.", "red"))
                else:
                    print(colored(f"Mistral AI Error: {err}", "red"))
                return None
            except requests.exceptions.ConnectionError:
                print(colored("Failed.", "red"))
                print(colored("Mistral AI Error: 🌐 Connection failed. Check your network.", "red"))
                return None
        print(colored("Mistral AI Error: Max retries exceeded.", "red"))
        return None

    def query_huggingface(self, prompt, model=None):
        model = model or self.huggingface_model
        headers = {"Authorization": f"Bearer {self.huggingface_api_key}", "Content-Type": "application/json"}
        data = {"inputs": prompt, "parameters": {"max_length": 200, "temperature": 0.2}}
        
        for attempt in range(3):
            print(colored("Querying Hugging Face...", "yellow"), end="", flush=True)
            try:
                response = requests.post(f"https://api-inference.huggingface.co/models/{model}", json=data, headers=headers)
                response.raise_for_status()
                print(colored("Done.", "green"))
                result = response.json()
                return result[0]["generated_text"].strip() if isinstance(result, list