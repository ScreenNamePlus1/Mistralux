![](https://github.com/ScreenNamePlus1/Mistralux/blob/main/1755716278933.jpg)
# Mistralux: AI-Enhanced Linux Shell

Mistralux provides `AIShell`, a Python-based command-line shell that enhances Linux workflows with AI-powered features. It supports Mistral AI API, Hugging Face API, or local inference (using Hugging Face `transformers`) for natural language command generation, explanations, script generation, and file summarization.

## Features
- **Standard Commands**: Execute Linux commands (e.g., `ls -l`, `cd ..`, `git status`).
- **AI-Powered Commands**:
  - `natural <query>`: Converts natural language to Linux commands (e.g., `natural list all files` → `ls`).
  - `explain <command>`: Explains commands in simple terms (e.g., `explain grep -r`).
  - `generate_script <description>`: Creates Bash scripts from descriptions (e.g., `generate_script backup my home directory`).
  - `summarize <filename>`: Summarizes text files (e.g., `summarize README.md`).
- **AI Configuration**:
  - `switch_ai [mistral|huggingface|local]`: Switches between Mistral AI, Hugging Face APIs, or local inference.
  - `toggle_ai`: Toggles AI suggestions for command errors.
  - `alias <name>=<command>`: Defines command shortcuts (e.g., `alias ll=ls -l`).
- **Built-In Commands**:
  - `cd <path>`: Changes the current directory.
  - `pwd`: Prints the working directory.
  - `exit`: Exits the shell.
  - `help`: Lists available commands.
- **Interactive UI**:
  - Dynamic prompt showing AI provider, virtual environment, and directory (e.g., `[Local]aishell_venv:Mistralux $`).
  - Command history persistence (use arrow keys to recall commands).
  - Tab completion for commands (`natural`, `explain`, `switch_ai`) and files (`summarize`).
- **Safety Checks**: Blocks dangerous commands (e.g., `rm -rf /`, `sudo`, `chmod -R 777`).
- **Error Handling**: Suggests fixes for command errors, retries API rate limits, and handles timeouts (5s for commands, 10s for scripts).
- **Caching**: Caches API responses for faster repeated queries.

![](https://github.com/ScreenNamePlus1/Mistralux/blob/main/Screenshot_20250821-020312.png)

## Prerequisites
- Python 3.8+.
- For API mode (`mistral` or `huggingface`):
  - Mistral AI API key from [Mistral Console](https://console.mistral.ai/api-keys/).
  - Hugging Face API key from [Hugging Face Settings](https://huggingface.co/settings/tokens).
- For local mode (`local`):
  - 16GB+ RAM, ~13GB storage for `mistralai/Mistral-7B-Instruct-v0.2`.
  - Hugging Face model access (accept terms at [Hugging Face](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2)).
  - Dependencies: `transformers`, `torch`, `accelerate`, `bitsandbytes`.

## Installation and Setup for `aishell.py`
Supports Mistral AI, Hugging Face APIs, or local inference.

1. **Clone Repository**:
   ```bash
   git clone git@github.com:ScreenNamePlus1/Mistralux.git
   cd Mistralux
   ```

2. **Install Dependencies**:
   - For API mode:
     ```bash
     pip install requests termcolor
     ```
   - For local mode (optional):
     ```bash
     pip install transformers torch accelerate bitsandbytes --index-url https://download.pytorch.org/whl/cpu
     ```
   - **Known Issues**:
     - Ensure `requests` is 2.25+ (`pip show requests`). Update `pip`: `pip install --upgrade pip`.
     - SSL errors: Update Python to 3.8+ or install `certifi` (`pip install certifi`).
     - Local mode: Model download (~13GB) needs stable internet; interruptions may corrupt `~/.cache/huggingface` (delete and retry).
     - Local mode OOM: Use `load_in_4bit=True` or add system swap (e.g., 4GB).
     - Model access: Accept terms for `mistralai/Mistral-7B-Instruct-v0.2` at [Hugging Face](https://huggingface.co/mistralai). Use `huggingface-cli login` if prompted.
     - CPU performance is slow (10-30s/query); prefer API mode for speed.

3. **Set API Keys** (for `mistral` or `huggingface` modes):
   - Add to shell profile (`~/.bashrc` or `~/.zshrc`):
     ```bash
     nano ~/.bashrc
     ```
     Add:
     ```bash
     export MISTRAL_API_KEY=your_mistral_key
     export HUGGINGFACE_API_KEY=your_hf_token
     ```
     Save and reload:
     ```bash
     source ~/.bashrc
     ```

4. **Make Script Executable**:
   - Ensure shebang (`#!/usr/bin/env python3`) is at the top of `aishell.py`.
   - Set permissions and add to `$PATH`:
     ```bash
     chmod +x aishell.py
     mkdir -p ~/bin
     ln -s $(pwd)/aishell.py ~/bin/aishell
     echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
     source ~/.bashrc
     ```

## Termux-Specific Setup
For Android users running in Termux, using a virtual environment to manage dependencies and resources.

1. **Install Base Packages**:
   ```bash
   pkg install python git
   ```

2. **(Optional) Set Up Debian for Isolation**:
   ```bash
   pkg install proot-distro
   proot-distro install debian
   proot-distro login debian
   apt update
   apt install python3 git
   ```

3. **Clone Repository** (in Termux or Debian):
   ```bash
   git clone git@github.com:ScreenNamePlus1/Mistralux.git
   cd Mistralux
   ```

4. **Set Up Virtual Environment**:
   - Required to avoid dependency conflicts and manage Termux’s resource constraints:
     ```bash
     python3 -m venv aishell_venv
     source aishell_venv/bin/activate
     ```
   - Persist activation:
     ```bash
     nano ~/.zshrc
     ```
     Add:
     ```bash
     source ~/aishell_venv/bin/activate
     ```
     Save and reload:
     ```bash
     source ~/.zshrc
     ```

5. **Install Dependencies**:
   - For API mode:
     ```bash
     pip install requests cmd termcolor
     ```
     - **Known Issues**: SSL errors with old Python; update via `pkg install python`. Check `requests` version (`pip show requests`).
   - For local mode (optional, resource-intensive):
     ```bash
     pip install transformers torch accelerate bitsandbytes --index-url https://download.pytorch.org/whl/cpu
     ```
     - **Known Issues**:
       - Limited RAM causes OOM; add swap:
         ```bash
         fallocate -l 2G ~/swapfile
         chmod 600 ~/swapfile
         mkswap ~/swapfile
         swapon ~/swapfile
         ```
         Increase to 4G if needed.
       - Slow performance on CPU; prefer API mode (`mistral` or `huggingface`).

6. **Set API Keys** (for `mistral` or `huggingface` modes):
   - Add to `~/.zshrc` or `~/.bashrc`:
     ```bash
     nano ~/.zshrc
     ```
     Add:
     ```bash
     export MISTRAL_API_KEY=your_mistral_key
     export HUGGINGFACE_API_KEY=your_hf_token
     ```
     Save and reload:
     ```bash
     source ~/.zshrc
     ```

7. **Make Script Executable**:
   ```bash
   chmod +x aishell.py
   mkdir -p ~/bin
   ln -s $(pwd)/aishell.py ~/bin/aishell
   echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

## Usage
Run:
```bash
aishell
```
- **Prompt**: `[Provider]venv:directory $` (e.g., `[Local]aishell_venv:Mistralux $`).
- **Examples**:
  ```bash
  ls -l
  switch_ai local
  natural find all text files
  explain du -sh
  generate_script monitor disk space
  summarize README.md
  alias ll=ls -l
  toggle_ai
  cd ..
  pwd
  exit
  help
  ```

## Troubleshooting
- **API Key Errors**: Verify keys (`echo $MISTRAL_API_KEY`, `echo $HUGGINGFACE_API_KEY`) or check [Mistral Console](https://console.mistral.ai/api-keys/) / [Hugging Face Settings](https://huggingface.co/settings/tokens).
- **Dependency Conflicts**: Use Python 3.8+; update `pip` (`pip install --upgrade pip`) or reinstall packages.
- **Network Issues**: Test connectivity (`ping api.mistral.ai`, `ping api-inference.huggingface.co`).
- **Local Mode Issues**:
  - Model access: Accept terms at [Hugging Face](https://huggingface.co/mistralai). Use `huggingface-cli login`.
  - OOM: Increase swap or use API mode.
  - Slow performance: Expected on CPU; prefer API mode.
- **Termux-Specific**:
  - Reinstall Debian: `proot-distro remove debian && proot-distro install debian`.
  - Memory issues: Increase swap or use API mode.

## Files
- `aishell.py`: Shell with Mistral AI, Hugging Face API, and local inference support.
- `LICENSE`: Project license.
- `1755716278933.jpg`: Project image.
- `README.md`: This file.
