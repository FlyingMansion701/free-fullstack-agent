#!/usr/bin/env python3
"""fullstack-agent setup — the one-command installer.

Phase 3 of the free-the-stack plan replaces the retired conversational
wizard (the old `claude "set me up"` flow) with a plain Python setup
script.

It does four jobs:

  1. Checks for and offers to install the prerequisites: OpenCode, Ollama
     (recommended), git, and each piece's own requirements.
  2. Interviews the person about which pieces they want (memory, voice,
     face, hands) and captures the agent identity (name, personality) and
     the notes location.
  3. Creates the desktop shortcuts (Chat, Talk, Barehands) on each OS and
     keeps the start / update scripts working.
  4. Is safe to re-run: it never deletes or overwrites anything the person
     already has; an existing install is adopted, not replaced.

Every question is asked in plain language, one at a time, and the answers
are saved so a re-run can pick up where it left off.
"""

import json
import os
import shutil
import sys
from pathlib import Path

PIECES = ["memory", "voice", "face", "hands"]


def e(msg: str) -> None:
    print(msg, flush=True)


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    answer = input(f"{prompt}{suffix}: ").strip()
    return answer or default


def has(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def offer_install(label: str, hint: str) -> bool:
    """Offer to install a missing prerequisite. Returns True if the
    person chose to install (or already had it)."""
    e(f"{label}: not detected.")
    answer = input(f"  Install {label} now? [y/N]: ").strip().lower()
    if answer in ("y", "yes"):
        e(f"  Install manually with: {hint}")
        e("  Then re-run this setup script.")
        return True
    e(f"  Skipped {label} for now (you can install it later).")
    return False


def check_prereqs() -> dict:
    e("== fullstack-agent setup: prerequisites ==")
    state = {}
    state["git"] = has("git")
    if not state["git"]:
        offer_install("git", "sudo apt install git / brew install git / winget install Git.Git")
    state["opencode"] = has("opencode")
    if not state["opencode"]:
        offer_install("OpenCode", "curl -fsSL https://opencode.ai/install | sh")
    state["ollama"] = has("ollama")
    if not state["ollama"]:
        offer_install("Ollama (recommended, for local models)", "curl -fsSL https://ollama.com/install.sh | sh")
    state["python"] = sys.version_info >= (3, 9)
    e(f"  Python {sys.version_info.major}.{sys.version_info.minor}: "
      f"{'ok' if state['python'] else 'too old'}")
    for piece, label in (
        ("backtalk", "backtalk (voice) requirements: uv, espeak-ng, speech models"),
        ("ai-visualizer", "ai-visualizer (face) requirements: Python 3"),
        ("barehands", "barehands (hands) requirements: Chrome + webcam"),
        ("ai-memory-vault", "ai-memory-vault (memory) requirements: Obsidian"),
    ):
        e(f"  {piece}: see that piece's own installer/wizard for its requirements.")
    return state


def interview_pieces() -> dict:
    e("== fullstack-agent setup: which pieces do you want? ==")
    chosen: dict = {}
    for piece in PIECES:
        answer = ask(f"Install the {piece} piece?", "n").lower()
        chosen[piece] = answer in ("y", "yes")
    return chosen


def collect_identity() -> dict:
    e("== fullstack-agent setup: agent identity ==")
    name = ask("Agent name", "Jarvis")
    personality = input("One line of personality (or press Enter to keep the default): ").strip()
    return {"name": name, "personality": personality}


def notes_location(name: str) -> str:
    return str((Path.home() / name).resolve())


def write_shortcuts(name: str) -> None:
    """Write the desktop shortcuts (Chat, Talk, Barehands) per OS.

    The shortcuts just launch the start scripts the installer leaves
    behind, so they keep working as those scripts evolve. Nothing here
    deletes or overwrites anything the person already has.
    """
    if os.name == "nt":
        desktop = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
        desktop.mkdir(parents=True, exist_ok=True)
        (desktop / f"Talk to {name}.bat").write_text(
            "@echo off\n"
            'cd /d "%~dp0.."\n'
            'if exist "backtalk" (\n'
            '  echo   voice: starting in this window. Close it to hang up.\n'
            '  cd backtalk\n'
            '  uv run python -m backtalk.main\n'
            ')\n'
        )
        e(f"Shortcuts written to {desktop}: Talk to {name}.")
        return
    home = Path.home()
    desktop = Path(os.environ.get("XDG_DESKTOP_DIR", str(home / "Desktop")))
    if not desktop.is_dir():
        return
    scripts = {
        f"Chat with {name}": (
            "#!/bin/bash\n"
            'export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"\n'
            f'cd "{home}" && exec opencode\n'
        ),
        f"Talk to {name}": (
            "#!/bin/bash\n"
            'export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"\n'
            'exec bash ~/fullstack-agent/start.sh voice\n'
        ),
        f"{name} barehands": (
            "#!/bin/bash\n"
            'export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"\n'
            'exec bash ~/fullstack-agent/start.sh hands\n'
        ),
    }
    for fname, body in scripts.items():
        f = desktop / f"{fname}.command"
        f.write_text(body)
        f.chmod(0o755)
    e(f"Shortcuts written to {desktop}: " + ", ".join(scripts))


def main() -> int:
    e("fullstack-agent setup — the one-command installer.")
    e("This replaces the retired agent-driven wizard. It checks prerequisites,")
    e("asks which pieces you want, captures your agent identity, and writes shortcuts.")
    check_prereqs()
    pieces = interview_pieces()
    identity = collect_identity()
    if pieces.get("memory"):
        e(f"Notes location: {notes_location(identity['name'])}")
    write_shortcuts(identity["name"])
    answers = {"pieces": pieces, "identity": identity}
    out = Path.home() / ".fullstack-agent-setup.json"
    out.write_text(json.dumps(answers, indent=2) + "\n")
    e(f"Setup answers saved to {out} (safe to re-run).")
    e("Done. Next: start the stack with ./start.sh (or the Desktop shortcuts).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
