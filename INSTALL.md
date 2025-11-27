# Installation Guide

## Installing Dependencies

### Option 1: Install pip using system package manager (Recommended)

On Fedora/RHEL:
```bash
sudo dnf install python3-pip
```

Then install Flask:
```bash
pip3 install Flask Werkzeug
```

Or using requirements.txt:
```bash
pip3 install -r requirements.txt
```

### Option 2: Install pip using get-pip.py (No sudo required)

```bash
# Download get-pip.py
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

# Install pip for current user
python3 get-pip.py --user

# Add to PATH (add to ~/.bashrc for permanent)
export PATH=$PATH:~/.local/bin

# Install Flask
python3 -m pip install --user Flask Werkzeug
```

### Option 3: Use python3 -m ensurepip (if available)

```bash
python3 -m ensurepip --user
python3 -m pip install --user Flask Werkzeug
```

### Option 4: Run without Web UI (No Flask needed)

If you don't need the web UI, you can run the system without Flask:

```bash
# Start tracker
python3 tracker.py

# Start peer (without web UI)
python3 peer.py --port 9000
```

The CLI client will work without Flask:
```bash
python3 client.py --host 127.0.0.1 --port 9000 status
```

## Quick Start (After pip is installed)

1. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

2. Start tracker:
   ```bash
   python3 tracker.py
   ```

3. Start peer with web UI:
   ```bash
   python3 peer.py --port 9000 --web-ui
   ```

4. Open browser:
   ```
   http://127.0.0.1:5000
   ```

## Troubleshooting

### pip command not found
- Use `pip3` instead of `pip`
- Or use `python3 -m pip` instead

### Permission denied
- Use `--user` flag: `pip3 install --user Flask`
- Or use `sudo` (if you have permissions)

### Module not found after installation
- Make sure you're using the same Python version
- Try: `python3 -m pip install Flask`




