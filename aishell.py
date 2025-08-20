#!/usr/bin/env python3
# aishell.py
# A complete Python script for an AI-enhanced Linux command-line shell.
# It integrates Mistral AI for natural language command generation, explanations, and script automation.
# Requirements:
# - Python 3.x
# - Install dependencies: pip install requests cmd
# - Obtain a Mistral AI API key from https://mistral.ai and set it as an environment variable: export MISTRAL_API_KEY=your_key
# - Run the shell: python aishell.py

import subprocess
import os
import sys
import requests
from cmd import Cmd
import shlex
from functools import lru_cache
from termcolor import colored

class AIShell(Cmd):
    intro = colored("Welcome to AI Shell with Mistral AI integration. Type help or ? for assistance.\n", "green")
    prompt = "$ "
    mistral_api_key = os.getenv("MISTRAL_API_KEY")
    if not mistral_api_key:
        print(colored("Error: MISTRAL_API_KEY environment variable not set.", "red"))
        sys.exit(1)

    mistral_model = os.getenv("MISTRAL_MODEL", "mistral-large-latest")

    @lru_cache(maxsize=100)
    def query_mistral(self, prompt, model=None):
        model = model or self.mistral_model
        if "codestral" in model.lower():
            url = "https://codestral.mistral.ai/v1/chat/completions"
        else:
            url = "https://api.mistral.ai/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.mistral_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 200,
            "temperature": 0.2
        }

        print(colored("Querying AI...", "yellow"), end="", flush=True)

        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            print(colored("Done.", "green"))
            return response.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.HTTPError as err:
            print(colored("Failed.", "red"))
            if err.response.status_code == 400:
                print(colored(f"AI Error: 400 Client Error: Bad Request for url: {url}", "red"))
                print(colored(f"API Response: {err.response.json()}", "red"))
            elif err.response.status_code == 401:
                print(colored("AI Error: 🚫 Authentication failed. Please check your MISTRAL_API_KEY.", "red"))
            else:
                print(colored(f"AI Error: {err}", "red"))
            return None
        except requests.exceptions.ConnectionError:
            print(colored("Failed.", "red"))
            print(colored("AI Error: 🌐 Connection failed. Please check your network.", "red"))
            return None
        except Exception as e:
            print(colored("Failed.", "red"))
            print(colored(f"AI Error: {e}", "red"))
            return None

    def is_safe_command(self, command):
        dangerous_patterns = [
            "rm -rf /", "mkfs", "dd if=", ":(){ :|:& };:",
            "sudo", "poweroff", "reboot", "halt"
        ]
        command_lower = command.lower()
        if any(pattern in command_lower for pattern in dangerous_patterns):
            print(colored("Warning: Command blocked for safety reasons.", "red"))
            return False
        return True

    def default(self, line):
        if not line:
            return
        try:
            args = shlex.split(line)
            process = subprocess.Popen(line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            if stdout:
                print(stdout.strip())
            if stderr:
                print(colored(f"Error: {stderr.strip()}", "red"))
                self.suggest_fix(line, stderr)
        except Exception as e:
            print(colored(f"Execution Error: {e}", "red"))

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
            print(colored("Usage: natural <natural language query>", "red"))
            return
        prompt = f"Convert this natural language request to a single Linux command (output only the command): '{line}'"
        command = self.query_mistral(prompt, model="codestral-latest")
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
        prompt = f"Generate a Bash shell script for: '{line}'. Output only the script code."
        script = self.query_mistral(prompt, model="codestral-latest")
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
            summary = self.query_mistral(prompt, model="mistral-large-latest")

            if summary:
                print(colored("\n--- Summary ---", "green"))
                print(summary)
                print(colored("---------------", "green"))

        except FileNotFoundError:
            print(colored(f"Error: The file '{line}' was not found.", "red"))
        except Exception as e:
            print(colored(f"An error occurred: {e}", "red"))

    def do_cd(self, path):
        try:
            os.chdir(path)
            self.prompt = colored(f"{os.getcwd()} $ ", "blue")
        except Exception as e:
            print(colored(f"cd Error: {e}", "red"))

    def do_pwd(self, arg):
        print(os.getcwd())

    def do_exit(self, arg):
        print(colored("Exiting AI Shell.", "blue"))
        return True

    def do_help(self, arg):
        super().do_help(arg)
        print(colored("\nAI Features:", "cyan"))
        print(colored("  natural <query>       - Convert natural language to command", "white"))
        print(colored("  explain <command>     - Explain a command", "white"))
        print(colored("  generate_script <desc>- Generate a script from description", "white"))
        print(colored("  summarize <filename>  - Summarize a text file", "white"))
        print(colored("\nRegular commands: Any Linux command (e.g., ls, cat)", "magenta"))

if __name__ == "__main__":
    try:
        from termcolor import colored
    except ImportError:
        print("Note: The 'termcolor' library is not installed. To enable colored output, run: pip install termcolor")
        # Define a dummy colored function if not installed
        def colored(text, *args, **kwargs):
            return text

    AIShell().cmdloop()
