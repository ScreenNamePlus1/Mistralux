# aishell.py
# AI-enhanced Linux command-line shell using Hugging Face Transformers for local Mistral model inference.
# Requirements:
# - Python 3.x
# - Install dependencies: pip install transformers torch accelerate bitsandbytes
# - Hardware: GPU with 16GB+ VRAM recommended for Mistral models
# - Run: python aishell.py

import subprocess
import os
import sys
from cmd import Cmd
import shlex
from functools import lru_cache
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class AIShell(Cmd):
    intro = "Welcome to AI Shell with local Mistral model integration. Type help or ? for assistance.\n"
    prompt = "$ "
    
    def __init__(self):
        super().__init__()
        # Initialize the Mistral model and tokenizer
        self.model_name = "mistralai/Mistral-7B-Instruct-v0.2"  # Change to Mixtral-8x7B-Instruct-v0.1 for larger model
        print(f"Loading model {self.model_name}... This may take a few minutes.")
        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            # Load model with quantization for lower memory usage (optional)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                device_map="auto",  # Automatically place model on GPU/CPU
                torch_dtype=torch.float16,  # Use half-precision for efficiency
                # load_in_4bit=True,  # Uncomment for 4-bit quantization (requires bitsandbytes)
            )
            print("Model loaded successfully.")
        except Exception as e:
            print(f"Error loading model: {e}")
            sys.exit(1)
    
    @lru_cache(maxsize=100)
    def query_mistral(self, prompt, model=None):  # Model parameter ignored for compatibility with cache
        try:
            # Prepare the prompt with instruction format (Mistral's recommended format)
            messages = [{"role": "user", "content": prompt}]
            inputs = self.tokenizer.apply_chat_template(messages, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")
            
            # Generate response
            outputs = self.model.generate(
                inputs,
                max_new_tokens=200,
                temperature=0.2,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Extract only the assistant's response (remove prompt)
            response = response.split("Assistant:")[-1].strip() if "Assistant:" in response else response.strip()
            return response
        except Exception as e:
            print(f"Model Inference Error: {e}")
            return None
    
    def is_safe_command(self, command):
        dangerous_patterns = [
            "rm -rf /", "mkfs", "dd if=", ":(){ :|:& };:",
            "sudo", "poweroff", "reboot", "halt"
        ]
        command_lower = command.lower()
        if any(pattern in command_lower for pattern in dangerous_patterns):
            print("Warning: Command blocked for safety reasons.")
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
                print(f"Error: {stderr.strip()}")
                self.suggest_fix(line, stderr)
        except Exception as e:
            print(f"Execution Error: {e}")
    
    def suggest_fix(self, original_command, error):
        prompt = f"The Linux command '{original_command}' failed with error: '{error}'. Suggest a corrected command or explanation."
        suggestion = self.query_mistral(prompt)
        if suggestion:
            print(f"AI Suggestion: {suggestion}")
            if "command:" in suggestion.lower():
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
        command = self.query_mistral(prompt)
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
        script = self.query_mistral(prompt)
        if script:
            print("Generated Script:")
            print(script)
            filename = input("Save to file? Enter filename or press enter to skip: ")
            if filename:
                with open(filename, "w") as f:
                    f.write(script)
                print(f"Saved to {filename}")
            if input("Execute script? (y/n): ").lower() == "y":
                if self.is_safe_command(script):
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
