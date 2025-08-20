### This script creates a special command-line environment that combines a regular terminal with an AI assistant. After running it, you’ll see a `$` prompt for typing commands.

### Command Usage
- **Regular Commands**: Type Linux commands like `ls -l` (list files) or `cd ..` (change directory).
- **AI Features**: Use keywords to access AI tools:
  - `natural`: Convert sentences to commands (e.g., `natural find all text files`).
  - `explain`: Describe a command (e.g., `explain du -sh`).
  - `generate_script`: Create a script from a description (e.g., `generate_script a script to monitor disk space`).
  - `help`: Show available commands.
  - `exit`: Quit the shell.

### Overview
This script integrates standard terminal commands with AI-powered features in one interface.

### Project Structure
- **Single File**: Save as `aishell.py` for simplicity.
- **Optional Multi-File**:
  - `aishell/`
    - `__init__.py` (empty)
    - `main.py` (AIShell class and `cmdloop`)
    - `ai_utils.py` (query_mistral, is_safe_command)
    - `shell_commands.py` (do_natural, do_explain, etc.)
    - `requirements.txt` (e.g., `requests`)
- **Features**: Linux command execution (with piping/redirection), natural language to commands, explanations, script generation, error suggestions, security checks, caching (`lru_cache`), and built-in commands (cd, pwd, exit).

### General Installation and Usage
#### Prerequisites
1. **Python 3.x**: Install if missing (e.g., `sudo apt install python3 python3-pip` on Debian/Ubuntu, or use your package manager).
2. **Dependencies**: Install `requests`:
   ```bash
   pip3 install requests
   ```
3. **Mistral API Key**: Sign up at https://mistral.ai, get a key from https://console.mistral.ai/api-keys/, and set it:
   ```bash
   export MISTRAL_API_KEY=your_api_key_here
   ```

#### Steps
1. **Save the Script**: Create `aishell.py` in a directory (e.g., `~/projects/Mistralux`):
   ```bash
   mkdir -p ~/projects/Mistralux
   cd ~/projects/Mistralux
   nano aishell.py  # Paste code, save
   ```
2. **Run the Script**:
   ```bash
   python3 aishell.py
   ```
   - Expect: `Welcome to AI Shell... $`
3. **Usage Examples**:
   - `ls -l` (regular command)
   - `natural list all files recursively` (AI conversion)
   - `explain grep -r` (explanation)
   - `generate_script backup my home directory` (script)
   - Failed commands suggest fixes.
- **Note**: Uses Mistral’s API (check https://docs.mistral.ai). For local use, see `aishell_local.py`.

# Optional: Make Executable
- Add shebang: `#!/usr/bin/env python3` at the top.
- Run: `chmod +x ~/Mistralux/aishell.py` and `./aishell.py` to verify it is executable.

To add your script to your $PATH so it can be run from any folder, you should create a symbolic link in a directory that is already in your $PATH. Since you are not root, you can't use system directories like /usr/local/bin. The best practice is to use your personal ~/bin directory.

- Step 1: Create a personal bin directory
First, check if you have a bin directory in your home folder. If not, create it.
    mkdir -p ~/bin

- Step 2: Add ~/bin to your $PATH
To make this directory a part of your system's search path, you need to add it to your shell's configuration file.
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
    source ~/.bashrc

This command appends the line to your .bashrc file and then reloads the file so the changes take effect immediately.

- Step 3: Create a symbolic link to your script
Now, you can create a symbolic link (a shortcut) from your ~/bin directory to your script in ~/Mistralux. This lets you run the script from anywhere without moving the actual file.
    ln -s ~/Mistralux/aishell.py ~/bin/aishell

This command creates a link named aishell inside your ~/bin folder that points to your aishell.py script. Note that you don't need the .py extension for the link name, which makes it easier to type.

Now you can type aishell from anywhere within your venv or any environment you installed this in. I used a venv in Debian on Termux.


### Local Version (`aishell_local.py`) with No API Calls
Replaces the Mistral API with Hugging Face `transformers` for local inference.

#### Prerequisites
- **Hardware**: GPU (16GB+ VRAM preferred), 16-32GB RAM, ~13GB storage (Mistral-7B).
- **Dependencies**: Install:
  ```bash
  pip3 install transformers torch accelerate bitsandbytes
  ```
  - Use CUDA-enabled `torch` if GPU is available (see https://pytorch.org).
- **Model**: Use `mistralai/Mistral-7B-Instruct-v0.2` (accept terms at https://huggingface.co/mistralai if needed).

#### Modifications
- Replace `query_mistral` with local inference:
  - Load model in `__init__` with `device_map="auto"`, `torch_dtype=torch.float16`, and `load_in_4bit=True` (for quantization).
  - Use `apply_chat_template`, generate 200 tokens.
- Keep `@lru_cache` for caching.

#### Run
1. **Save as `aishell_local.py`**: Same as above.
2. **Execute**:
   ```bash
   python3 aishell_local.py
   ```
   - Downloads model (~13GB) on first run.
3. **Usage**: Same as `aishell.py`.

#### Considerations
- **Performance**: GPU is faster; CPU is slow (10-30s per query).
- **Memory**: Use quantization or offload to CPU if needed.
- **Login**: Use `huggingface-cli login` if required (token from https://huggingface.co/settings/tokens).

### Virtual Environment Setup for Debian on Termux
Create an isolated Python environment in Debian on Termux.

1. **Enter Debian**:
   ```bash
   proot-distro login debian
   ```
2. **Install Tools**:
   ```bash
   apt update
   apt install python3 python3-venv
   ```
3. **Create Venv**:
   ```bash
   python3 -m venv ~/aishell_venv
   source ~/aishell_venv/bin/activate
   ```
   - Prompt changes (e.g., `(aishell_venv)`).
4. **Deactivate** (when done):
   ```bash
   deactivate
   ```

### Termux Instructions
Run `aishell.py` or `aishell_local.py` in Debian on Termux.

#### Setup
1. **Install Debian**:
   ```bash
   pkg install proot-distro
   proot-distro install debian
   proot-distro login debian
   apt update
   ```
2. **Set Up Venv** (Not Optional): Follow the "Virtual Environment Setup" above.
3. **Clone Repository**:
   ```bash
   apt install git
   git clone https://github.com/ScreenNamePlus1/Mistralux.git
   cd Mistralux
   ```
4. **For `aishell.py`**:
   - Install: `pip3 install requests`
   - Set API Key: `export MISTRAL_API_KEY=your_api_key_here` (from https://console.mistral.ai/api-keys/).
   - Run: `python3 aishell.py`
5. **For `aishell_local.py`**:
   - Install: `pip3 install transformers torch --index-url https://download.pytorch.org/whl/cpu accelerate bitsandbytes`
   - Add Swap: `fallocate -l 2G ~/swapfile && chmod 600 ~/swapfile && mkswap ~/swapfile && swapon ~/swapfile`
   - Edit: Ensure `load_in_4bit=True` in `aishell_local.py`.
   - Run: `python3 aishell_local.py` (needs ~13GB, check with `df -h ~`).

#### Usage
- Use: `ls`, `natural list all files`, `help`, `exit`.
- Prefer `aishell.py` due to Termux’s resource limits.

#### Troubleshooting
- **API Key**: Recheck if “401 Unauthorized” (https://console.mistral.ai/api-keys/).
- **Torch**: Use CPU wheel or Python 3.10 if needed.
- **Memory**: Increase swap to 4G if out of memory.
- **Debian**: Reinstall with `proot-distro remove debian` and `proot-distro install debian`.

### To make your Mistral API key persistent in Termux, you can add it to your shell configuration file so it’s available every time you open a new session. Here’s how:

1. Open or edit your shell profile file (e.g., `~/.bashrc` or `~/.profile`) in Debian on Termux:
   ```bash
   nano ~/.bashrc
   ```
   - If `~/.bashrc` doesn’t exist or you prefer another file, use `nano ~/.profile`.

2. Add the following line at the end of the file, replacing `your_api_key_here` with your actual Mistral API key:
   ```bash
   export MISTRAL_API_KEY=your_api_key_here
   ```

3. Save the file and exit:
   - Press `Ctrl + O`, then `Enter` to save, and `Ctrl + X` to exit in nano.

4. Apply the changes to your current session:
   ```bash
   source ~/.bashrc
   ```
   - Or, if you used `~/.profile`, run `source ~/.profile`.

Now, the API key will be available in future Termux sessions without needing to export it manually each time. To verify, you can run `echo $MISTRAL_API_KEY` and check if it displays the key.

## You might say "This is so annoying opening so many things every time I open Termux...

Yes, you can configure Termux to automatically activate a virtual environment (venv) every time you open it. This is done by adding the activation command to your shell's startup file.
For most Termux users, the default shell is Bash. The startup file for Bash is ~/.bashrc. If you are using a different shell like Zsh, the file would be ~/.zshrc.
Here is a step-by-step guide:

### Step 1: 
Create or Locate your venv
First, you need a virtual environment. If you don't have one, navigate to the directory where you want it and create it with this command:
    python -m venv my_env

(You can replace my_env with whatever name you want for your environment.)
This will create a new directory called my_env with the virtual environment inside.

### Step 2: 
Edit your Shell's Startup File
You will now add a line to the ~/.bashrc file (or ~/.zshrc).
 * Open the file with a text editor. You can use a simple one like nano:
   nano ~/.bashrc

(or nano ~/.zshrc if you are using Zsh)

 * Move to the very end of the file.
 * Add the following two lines. The first line is a comment to remind you what this code does. The second line is the command that activates the virtual environment.

    # Automatically activate my_env when Termux starts
source ~/path/to/my_env/bin/activate

### Important: 
You must replace ~/path/to/my_env with the actual path to your virtual environment. If your my_env is in your home directory, the path would be ~/my_env.
 * Press Ctrl + S to save the file and Ctrl + X to exit nano.

### Step 3: 
Test It
Close Termux and reopen it. The virtual environment should activate automatically. You will know it's working if you see the name of your virtual environment (e.g., (my_env)) at the beginning of your command prompt.

### To set your api key automatically when you open Termux

Open ~/.zshrc and add 

    export MISTRAL_API_KEY="<your><api><key>"

to the top somewhere. If you activate your venv using this method, add it below that.