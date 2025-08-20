# aishell.py
# This is a complete Python script for an AI-enhanced Linux command-line shell.
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
import shlex  # For parsing commands with quotes and escapes
from functools import lru_cache  # For simple caching

class AIShell(Cmd):
    intro = "Welcome to AI Shell with Mistral AI integration. Type help or ? for assistance.\n"
    prompt = "S̵̙͕̀̃c͕͗ͤ̕̕r̴̨̦͕̝ẹ̿͋̒̕ẹ̿͋̒̕ṇ̤͛̒̍N̺̻̔̆ͅā̤̓̍͘ḿ̬̏ͤͅẹ̿͋̒̕P̧͕̒̊͘l̙͖̑̾ͣư̡͕̭̇s̠҉͍͊ͅ1̨̹̦͍̀
 "
    mistral_api_key = os.getenv("MISTRAL_API_KEY")
    if not mistral_api_key:
        print("Error: MISTRAL_API_KEY environment variable not set.")
        sys.exit(1)

    # Cache for AI responses to reduce API calls (up to 100 recent calls)
    @lru_cache(maxsize=100)
    def query_mistral(self, prompt, model="mistral-large-latest"):
        # Use the correct URL based on the model
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
            "temperature": 0.2  # Low temperature for deterministic responses
        }
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 400:
                print(f"AI Error: 400 Client Error: Bad Request for url: {url}")
                print(f"API Response: {err.response.json()}")
            else:
                print(f"AI Error: {err}")
            return None
        except Exception as e:
            print(f"AI Error: {e}")
            return None

    def is_safe_command(self, command):
        # Basic security: Block potentially dangerous commands
        dangerous_patterns = [
            "rm -rf /", "mkfs", "dd if=", ":(){ :|:& };:",  # Fork bomb, etc.
            "sudo", "poweroff", "reboot", "halt"  # System-level commands
        ]
        command_lower = command.lower()
        if any(pattern in command_lower for pattern in dangerous_patterns):
            print("Warning: Command blocked for safety reasons.")
            return False
        return True

    def default(self, line):
        # Handle regular Linux commands
        if not line:
            return
        try:
            # Parse the line to handle pipes, redirects, etc.
            args = shlex.split(line)
            process = subprocess.Popen(line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            if stdout:
                print(stdout.strip())
            if stderr:
                print(f"Error: {stderr.strip()}")
                # Suggest fix if error
                self.suggest_fix(line, stderr)
        except Exception as e:
            print(f"Execution Error: {e}")

    def suggest_fix(self, original_command, error):
        # Use AI to suggest a fix for failed commands
        prompt = f"The Linux command '{original_command}' failed with error: '{error}'. Suggest a corrected command or explanation."
        suggestion = self.query_mistral(prompt)
        if suggestion:
            print(f"AI Suggestion: {suggestion}")
            if "command:" in suggestion.lower():
                # Extract suggested command if present
                suggested_cmd = suggestion.split("command:")[-1].strip()
                if input(f"Execute suggested command '{suggested_cmd}'? (y/n): ").lower() == "y":
                    if self.is_safe_command(suggested_cmd):
                        self.default(suggested_cmd)

    def do_natural(self, line):
        """Convert natural language to Linux command: natural <query>"""
        if not line:
            print("Usage: natural <natural language query>")
            return
        prompt = f"Convert this natural language request to a single Linux command (output only the command): '{line}'"
        command = self.query_mistral(prompt, model="codestral-latest")
        if command:
            print(f"Suggested command: {command}")
            if input("Execute? (y/n): ").lower() == "y":
                if self.is_safe_command(command):
                    self.default(command)

    def do_explain(self, line):
        """Explain a Linux command: explain <command>"""
        if not line:
            print("Usage: explain <command>")
            return
        prompt = f"Explain the Linux command '{line}' in simple terms."
        explanation = self.query_mistral(prompt)
        if explanation:
            print(explanation)

    def do_generate_script(self, line):
        """Generate a shell script from natural language: generate_script <description>"""
        if not line:
            print("Usage: generate_script <script description>")
            return
        prompt = f"Generate a Bash shell script for: '{line}'. Output only the script code."
        script = self.query_mistral(prompt, model="codestral-latest")
        if script:
            print("Generated Script:")
            print(script)
            filename = input("Save to file? Enter filename or press enter to skip: ")
            if filename:
                with open(filename, "w") as f:
                    f.write(script)
                print(f"Saved to {filename}")
            if input("Execute script? (y/n): ").lower() == "y":
                if self.is_safe_command(script):  # Rough check; scripts are multi-line
                    subprocess.run(["bash", "-c", script], text=True)

    def do_cd(self, path):
        """Change directory: cd <path>"""
        try:
            os.chdir(path)
            self.prompt = f"{os.getcwd()} $ "
        except Exception as e:
            print(f"cd Error: {e}")

    def do_pwd(self, arg):
        """Print working directory"""
        print(os.getcwd())

    def do_exit(self, arg):
        """Exit the shell"""
        print("Exiting AI Shell.")
        return True

    def do_help(self, arg):
        """List available commands"""
        super().do_help(arg)
        print("\nAI Features:")
        print("  natural <query>       - Convert natural language to command")
        print("  explain <command>     - Explain a command")
        print("  generate_script <desc>- Generate a script from description")
        print("\nRegular commands: Any Linux command (e.g., ls, cat)")

if __name__ == "__main__":
    AIShell().cmdloop()
