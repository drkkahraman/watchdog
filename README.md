#  Watchdog: Docker & Service Status Monitor (TUI)

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=flat-square&logo=python)](https://python.org)
[![Textual](https://img.shields.io/badge/Built%20with-Textual-brightgreen.svg?style=flat-square)](https://textual.textualize.io)
[![Docker](https://img.shields.io/badge/Docker-SDK-2496ED.svg?style=flat-square&logo=docker)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![CI](https://img.shields.io/badge/CI-Passing-success.svg?style=flat-square&logo=githubactions)](.github/workflows/ci.yml)

**A blazing-fast, lightweight, and modern Terminal User Interface (TUI) dashboard for real-time Docker container management, host system telemetry, and reverse proxy port tracking.**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Keybindings](#-keyboard-shortcuts) • [Docker](#-docker-quickstart)

</div>

```text
__        __  _  _____  ____  _   _  ____    ___    ____ 
 \ \      / / / \|_   _|/ ___|| | | ||  _ \  / _ \  / ___|
  \ \ /\ / / / _ \ | | | |    | |_| || | | || | | || | __ 
   \ V  V / / ___ \| | | |___ |  _  || |_| || |_| || |_\ \
    \_/\_/ /_/   \_\_|  \____||_| |_||____/  \___/  \____/
                                                         
   Real-time Docker & Service Monitor for Homelabs and Servers
```

---

## ⚡ Why Watchdog?

Heavy monitoring platforms like **Grafana / Prometheus / Portainer** require dedicated services, complex configurations, databases, and consume significant host memory and CPU. 

**Watchdog** runs natively in your terminal with a single command, consumes negligible resources, connects directly to your local or remote Docker daemon, and provides instant observability and management at your fingertips.

---

##  Features

-  **Live Container Dashboard**: Real-time stats for CPU %, Memory usage/limits, Network I/O (Rx/Tx), Block I/O (Read/Write), PIDs, and Healthcheck statuses.
- ⚡ **Single-Keystroke Lifecycle Management**:
  - `[R]` Restart container (with grace period & async progress toast)
  - `[S]` Start / Stop container (with confirmation dialog)
  - `[P]` Pause / Unpause container execution
  - `[L]` Open real-time streaming log viewer
  - `[I]` Inspect deep container attributes, environment variables, mounts, and network configuration
  - `[X]` Delete / Kill container safely with confirmation
-  **Reverse Proxy & Port Mapping Auto-Discovery**:
  - Automatically identifies container port forwardings (`Host IP:Port -> Container Port`).
  - Auto-detects reverse proxy routing labels from **Traefik**, **Caddy**, and **Nginx Proxy Manager / VIRTUAL_HOST**.
  - Highlights TLS/SSL secured endpoints.
-  **Host System Telemetry**:
  - Host CPU load %, Cores, Frequency.
  - Memory & Swap usage in real-time.
  - Disk storage capacity and utilization.
  - Real-time Network upload/download bandwidth speed (MB/s, KB/s).
  - Docker daemon version, engine status, and container tally.
-  **Fuzzy Search & Filtering**: Press `/` or `f` to instantly filter containers and services by name, status, image, or port.
-  **Modern Cyberpunk/Nord Aesthetic**: Crafted with rich colors, status badges, clean tables, and fluid keyboard navigation.

---

## 🚀 Installation

### Option 1: One-Liner Quick Install (No manual venv needed)

Install Watchdog globally to your system in a single command:

```bash
curl -sSL https://raw.githubusercontent.com/drkkahraman/watchdog/main/install.sh | bash
```

---

### Option 2: Using `pipx` (Recommended for Python CLI apps)

[`pipx`](https://pypa.github.io/pipx/) installs the CLI in an isolated environment automatically and makes the `watchdog` command globally accessible everywhere:

```bash
# Install directly from GitHub
pipx install git+https://github.com/drkkahraman/watchdog.git

# Or install from local directory
pipx install .

# Run from any terminal!
watchdog
```

---

### Option 3: Using `pip --user` (Global User Install)

```bash
# Global user installation without virtualenv
python3 -m pip install --user .

# Or directly from GitHub
python3 -m pip install --user git+https://github.com/drkkahraman/watchdog.git
```

> **Note**: Make sure `~/.local/bin` is in your `PATH`. If not, add `export PATH="$HOME/.local/bin:$PATH"` to your `~/.bashrc` or `~/.zshrc`.

---

### Option 4: From Source (Development / Virtual Environment)

```bash
# 1. Clone repository
git clone https://github.com/drkkahraman/watchdog.git
cd watchdog

# 2. Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install in editable mode
pip install -e ".[dev]"

# 4. Run Watchdog
watchdog
```

---

## 🐳 Docker Quickstart

Run Watchdog without installing Python dependencies using Docker:

```bash
# Run directly with Docker
docker run -it --rm \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  ghcr.io/doruk/watchdog:latest
```

Or using **Docker Compose**:

```yaml
version: "3.8"
services:
  watchdog:
    image: ghcr.io/doruk/watchdog:latest
    container_name: watchdog
    stdin_open: true
    tty: true
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
```

```bash
docker compose run --rm watchdog
```

---

## 🎮 Usage & CLI Options

```bash
# Launch default monitor
watchdog

# Custom polling interval (e.g., update every 1 second)
watchdog -i 1.0

# Connect to a remote Docker daemon via TCP or custom socket
watchdog -H tcp://192.168.1.100:2375
watchdog -H unix:///var/run/docker.sock

# Show version
watchdog --version
```

---

## ⌨️ Keyboard Shortcuts

| Key | Action | Description |
|---|---|---|
| `1` | **Containers View** | Switch to the main containers & resource statistics tab |
| `2` | **Services View** | Switch to reverse proxy & port mappings matrix |
| `r` | **Restart** | Trigger graceful container restart |
| `s` | **Start / Stop** | Toggle container start/stop (prompts confirmation for stop) |
| `p` | **Pause / Unpause** | Suspend or resume container execution |
| `l` | **Live Logs** | Open real-time streaming log viewer with tail & filter |
| `i` | **Inspect** | View environment variables, mounts, networks & raw JSON |
| `x` / `d` | **Remove** | Safely delete container with confirmation modal |
| `/` or `f` | **Filter / Search** | Focus search input to filter containers and services |
| `?` | **Help** | Open shortcut cheatsheet dialog |
| `q` | **Quit** | Exit Watchdog cleanly |

### In Log Viewer Modal:
- `Space`: Pause / Resume live log stream
- `Tail Buttons`: Switch between last 100, 500, or 1000 lines
- `Search Bar`: Filter log lines by text or regex
- `Esc` / `q`: Close log modal

---

## 🧪 Testing & Validation

Run unit tests and linters:

```bash
# Run all tests
pytest -v

# Run linter
ruff check .
```

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
