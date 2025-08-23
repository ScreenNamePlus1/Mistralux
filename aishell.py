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
                return result[0]["generated_text"].strip() if isinstance(result, list) else result.get("generated_text", "").strip()
            except requests.exceptions.HTTPError as err:
                print(colored("Failed.", "red"))
                if err.response.status_code == 429:
                    print(colored("Hugging Face Error: Rate limit exceeded. Retrying...", "yellow"))
                    time.sleep(2 ** attempt)
                    continue
                elif err.response.status_code == 401:
                    print(colored("Hugging Face Error: 🚫 Authentication failed. Check HUGGINGFACE_API_KEY.", "red"))
                else:
                    print(colored(f"Hugging Face Error: {err}", "red"))
                return None
            except requests.exceptions.ConnectionError:
                print(colored("Failed.", "red"))
                print(colored("Hugging Face Error: 🌐 Connection failed. Check your network.", "red"))
                return None
        print(colored("Hugging Face Error: Max retries exceeded.", "red"))
        return None

    def is_safe_command(self, command):
        dangerous_patterns = [
            "rm -rf /", "mkfs", "dd if=", ":(){ :|:& };:",
            "sudo", "poweroff", "reboot", "halt",
            "chmod -R 777", "chown -R", "curl.*|.*sh"
        ]
        command_lower = command.lower()
        if any(pattern in command_lower for pattern in dangerous_patterns):
            print(colored(f"Warning: Command '{command}' blocked for safety reasons.", "red"))
            return False
        return True

    def default(self, line):
        if not line:
            return
        if line in self.aliases:
            line = self.aliases[line]
        if not self.is_safe_command(line):
            return
        try:
            args = shlex.split(line)
            process = subprocess.Popen(line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate(timeout=5)
            if stdout:
                print(stdout.strip())
            if stderr:
                print(colored(f"Error: {stderr.strip()}", "red"))
                if self.use_ai:
                    self.suggest_fix(line, stderr)
        except subprocess.TimeoutExpired:
            print(colored("Error: Command timed out after 5 seconds.", "red"))
            if self.use_ai:
                self.suggest_fix(line, "Command timed out after 5 seconds.")
        except subprocess.SubprocessError as e:
            print(colored(f"Execution Error: {e}", "red"))
            if self.use_ai:
                self.suggest_fix(line, str(e))
        except Exception as e:
            print(colored(f"Unexpected Error: {e}", "red"))

    def suggest_fix(self, original_command, error):
        prompt = f"The Linux command '{original_command}' failed with error: '{error}'. Suggest a corrected command or explanation."
        suggestion = self.query_mistral(prompt)
        if suggestion:
            print(colored(f"AI Suggestion: {suggestion}", "cyan"))
            if "command:" in suggestion.lower():
                suggested_cmd = suggestion.split("command:")[-1].strip()
                if input(colored(f"Execute suggested command '{suggested_cmd}'? (y/n): ", "yellow")).lower() == "y":
                    if self.is_safe_command(suggested_cmd):
                        self.default(suggested_cmd)

    def do_natural(self, line):
        """Convert natural language to Linux command: natural <query>"""
        if not line:
            print(colored("Usage: natural <query>", "red"))
            return
        model = "codestral-latest" if self.ai_provider == "mistral" else None
        prompt = f"Convert this natural language request to a single Linux command (output only the command): '{line}'"
        command = self.query_mistral(prompt, model=model)
        if command:
            print(colored(f"Suggested command: {command}", "green"))
            if input(colored("Execute? (y/n): ", "yellow")).lower() == "y":
                if self.is_safe_command(command):
                    try:
                        subprocess.run(command, shell=True, check=True, text=True, capture_output=True, timeout=10)
                    except subprocess.CalledProcessError as e:
                        print(colored(f"Execution Error: The command returned a non-zero exit code.\n{e.stderr}", "red"))
                    except subprocess.TimeoutExpired:
                        print(colored("Execution Error: The command timed out.", "red"))

    def do_explain(self, line):
        """Explain a Linux command: explain <command>"""
        if not line:
            print(colored("Usage: explain <command>", "red"))
            return
        prompt = f"Explain the Linux command '{line}' in simple terms."
        explanation = self.query_mistral(prompt)
        if explanation:
            print(colored(explanation, "cyan"))

    def do_generate_script(self, line):
        """Generate a shell script from natural language: generate_script <description>"""
        if not line:
            print(colored("Usage: generate_script <script description>", "red"))
            return
        model = "codestral-latest" if self.ai_provider == "mistral" else None
        prompt = f"Generate a Bash shell script for: '{line}'. Output only the script code."
        script = self.query_mistral(prompt, model=model)
        if script:
            print(colored("Generated Script:", "green"))
            print(script)
            filename = input(colored("Save to file? Enter filename or press enter to skip: ", "yellow"))
            if filename:
                with open(filename, "w") as f:
                    f.write(script)
                print(colored(f"Saved to {filename}", "green"))
            if input(colored("Execute script? (y/n): ", "yellow")).lower() == "y":
                if self.is_safe_command(script):
                    try:
                        subprocess.run(["bash", "-c", script], check=True, text=True, capture_output=True, timeout=10)
                    except subprocess.CalledProcessError as e:
                        print(colored(f"Execution Error: The script returned a non-zero exit code.\n{e.stderr}", "red"))
                    except subprocess.TimeoutExpired:
                        print(colored("Execution Error: The script timed out.", "red"))

    def do_summarize(self, line):
        """Summarize a text file: summarize <filename>"""
        if not line:
            print(colored("Usage: summarize <filename>", "red"))
            return
        try:
            with open(line, "r") as f:
                text = f.read()
            prompt = f"Summarize the following text in a concise paragraph:\n\n{text}"
            summary = self.query_mistral(prompt)
            if summary:
                print(colored("\n--- Summary ---", "green"))
                print(summary)
                print(colored("--- End Summary ---", "green"))
        except FileNotFoundError:
            print(colored(f"Error: The file '{line}' was not found.", "red"))
        except Exception as e:
            print(colored(f"An error occurred: {e}", "red"))

    def do_switch_ai(self, arg):
        """Switch AI provider: switch_ai [mistral|huggingface|local]"""
        if arg.lower() not in ["mistral", "huggingface", "local"]:
            print(colored("Usage: switch_ai [mistral|huggingface|local]", "red"))
            return
        if arg.lower() == "local" and not self.local_model:
            if not pipeline:
                print(colored("Error: transformers library not installed. Install with: pip install transformers torch", "red"))
                return
            print(colored("Initializing local model...", "yellow"))
            try:
                self.local_model = pipeline("text-generation", model="mistralai/Mistral-7B-Instruct-v0.2",
                                           device=-1, load_in_4bit=True)
            except Exception as e:
                print(colored(f"Failed to load local model: {e}", "red"))
                return
        self.ai_provider = arg.lower()
        print(colored(f"AI provider set to {self.ai_provider}", "green"))
        self.update_prompt()

    def do_toggle_ai(self, arg):
        """Toggle AI suggestions on/off"""
        self.use_ai = not self.use_ai
        print(colored(f"AI suggestions {'enabled' if self.use_ai else 'disabled'}", "green"))

    def do_alias(self, line):
        """Define an alias: alias <name>=<command>"""
        if "=" not in line:
            print(colored("Usage: alias <name>=<command>", "red"))
            return
        name, cmd = line.split("=", 1)
        self.aliases[name.strip()] = cmd.strip()
        print(colored(f"Alias '{name}' set to '{cmd}'", "green"))

    def do_cd(self, path):
        """Change directory: cd <path>"""
        try:
            os.chdir(path)
            self.update_prompt()
        except Exception as e:
            print(colored(f"cd Error: {e}", "red"))

    def do_pwd(self, arg):
        """Print working directory"""
        print(os.getcwd())

    def do_exit(self, arg):
        """Exit the shell"""
        print(colored("Exiting AI Shell.", "blue"))
        return True

    def do_help(self, arg):
        """Show this help message"""
        super().do_help(arg)
        print(colored("\nAI Features:", "cyan"))
        print(colored("  natural <query>       - Convert natural language to command", "white"))
        print(colored("  explain <command>     - Explain a command", "white"))
        print(colored("  generate_script <desc>- Generate a script from description", "white"))
        print(colored("  summarize <filename>  - Summarize a text file", "white"))
        print(colored("  switch_ai [mistral|huggingface|local] - Switch AI provider", "white"))
        print(colored("  toggle_ai            - Toggle AI suggestions on/off", "white"))
        print(colored("  alias <name>=<cmd>   - Define a command alias", "white"))
        print(colored("\nStandard Commands:", "cyan"))
        print(colored("  cd <path>            - Change directory", "white"))
        print(colored("  pwd                  - Print working directory", "white"))
        print(colored("  exit                 - Exit the shell", "white"))
        print(colored("\nRegular Commands: Any Linux command (e.g., ls, cat)", "magenta"))

    def complete_natural(self, text, line, begidx, endidx):
        return [cmd for cmd in ["ls", "cd", "cat", "pwd", "git"] if cmd.startswith(text)] + glob.glob(text + "*")

    def complete_explain(self, text, line, begidx, endidx):
        return self.complete_natural(text, line, begidx, endidx)

    def complete_summarize(self, text, line, begidx, endidx):
        return glob.glob(text + "*")

    def complete_switch_ai(self, text, line, begidx, endidx):
        return [provider for provider in ["mistral", "huggingface", "local"] if provider.startswith(text)]

if __name__ == "__main__":
    print("Debug: Starting main block")
    try:
        from termcolor import colored
        print("Debug: termcolor re-imported successfully in main")
    except ImportError:
        print("Note: The 'termcolor' library is not installed. To enable colored output, run: pip install termcolor")
        def colored(text, *args, **kwargs):
            return text
    print("Debug: Creating AIShell instance")
    shell = AIShell()
    print("Debug: Starting cmdloop")
    shell.cmdloop()