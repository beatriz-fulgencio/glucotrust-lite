#!/usr/bin/env bash
# Bootstrap GlucoTrust from any working directory.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./init.sh [--run] [--skip-model] [--resolve-deps]

Create/reuse .venv, install dependencies, create .env if missing, and cache MiniLM.

  --run           Start the Streamlit app after setup.
  --skip-model    Skip downloading model weights (the app may download them later).
  --resolve-deps  Resolve dependencies instead of using the macOS ARM Python 3.12 lock.
  -h, --help      Show this help.

Set PYTHON to a Python 3.12+ executable when creating a new environment.
An existing .venv is reused. Existing .env values are never overwritten.
EOF
}

run_app=false
download_model=true
resolve_deps=false
for arg in "$@"; do
  case "$arg" in
    --run) run_app=true ;;
    --skip-model) download_model=false ;;
    --resolve-deps) resolve_deps=true ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown option: %s\n' "$arg" >&2; usage >&2; exit 2 ;;
  esac
done

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$project_dir"

supports_python() {
  "$1" -c 'import sys; sys.exit(sys.version_info < (3, 12))' >/dev/null 2>&1
}

if [[ -e .venv || -L .venv ]]; then
  if ! supports_python "$project_dir/.venv/bin/python"; then
    printf 'Existing .venv needs a working Python 3.12+. Move it aside and rerun setup.\n' >&2
    exit 1
  fi
else
  python_bin="${PYTHON:-}"
  if [[ -n "$python_bin" ]]; then
    if ! supports_python "$python_bin"; then
      printf 'PYTHON must point to a working Python 3.12+ executable.\n' >&2
      exit 1
    fi
  else
    for candidate in python3.12 /opt/homebrew/bin/python3.12 python3 python; do
      if supports_python "$candidate"; then
        python_bin="$candidate"
        break
      fi
    done
    if [[ -z "$python_bin" ]]; then
      printf 'Python 3.12+ is required. Install it and rerun, or set PYTHON=/path/to/python.\n' >&2
      exit 1
    fi
  fi
  printf 'Creating .venv with %s\n' "$python_bin"
  "$python_bin" -m venv .venv
fi

python_bin="$project_dir/.venv/bin/python"
if [[ ! -e .env && ! -L .env ]]; then
  cp .env.example .env
  printf 'Created .env. See .env.example for local Ollama settings.\n'
fi

platform_tag="$("$python_bin" -c 'import platform, sys; print(f"{platform.system()}-{platform.machine()}-{sys.version_info.major}.{sys.version_info.minor}")')"
if [[ "$resolve_deps" == false && "$platform_tag" == Darwin-arm64-3.12 ]]; then
  printf 'Installing dependencies from requirements.lock.txt\n'
  "$python_bin" -m pip install -r requirements.lock.txt
  "$python_bin" -m pip install . --no-deps --no-build-isolation
else
  printf 'Resolving compatible dependencies for %s\n' "$platform_tag"
  "$python_bin" -m pip install '.[dev]'
fi

if [[ "$download_model" == true ]]; then
  printf 'Downloading MiniLM weights (cached files are reused)\n'
  "$python_bin" -m scripts.download_model
fi

printf '\nSetup complete. Start Ollama and pull qwen3:4b-instruct-2507-q4_K_M for local assessments.\n'
if ! command -v ollama >/dev/null 2>&1; then
  printf 'Ollama is missing. Install it from https://ollama.com/download, then start it and pull the model.\n'
elif ! ollama list >/dev/null 2>&1; then
  printf 'Ollama is not reachable. Start the Ollama app or run ollama serve.\n'
elif ! ollama list | awk '{print $1}' | grep -Fxq 'qwen3:4b-instruct-2507-q4_K_M'; then
  printf 'Default assessment model is missing. Run: ollama pull qwen3:4b-instruct-2507-q4_K_M\n'
fi
if [[ "$run_app" == true ]]; then
  exec "$python_bin" -m streamlit run app.py
fi
printf 'Start the app: cd "%s" && .venv/bin/python -m streamlit run app.py\n' "$project_dir"
