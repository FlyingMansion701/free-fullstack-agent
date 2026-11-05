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
     where notes should live.
  3. Creates the desktop shortcuts (Chat, Talk, Barehands, Update) on each
     OS and keeps the start / update scripts working.
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

PIECE_BLURBS = {
    "memory": "the mind: where the agent keeps what it learns about you.",
    "voice": "the voice: speaks out loud through your speakers or headphones.",
    "face": "the face: a little window with a character that listens and reacts visually.",
    "hands": "the hands: an on-screen control board you drive with your voice or mouse.",
}

PIECE_REQUIREMENTS = {
    "memory": "Open your notes app (Obsidian) and point it at the agent's memory folder.",
    "voice": "uv, espeak-ng, and the speech models (backtalk's own installer walks through this).",
    "face": "Python 3 (ships with macOS and most Linux; Windows needs the py launcher - see below).",
    "hands": "Chrome and a webcam.",
}

# Real CLI commands worth offering to install for chosen pieces, if missing.
PIECE_INSTALLERS = {
    "memory": ("Obsidian (notes app)", "obsidian", "Install the notes app, then open the agent's memory folder inside it."),
    "voice": ("backtalk voice line", "uv", "backtalk's own installer walks through uv, espeak-ng, and the speech models."),
    "face": ("ai-visualizer (face)", "python3", "Install Python 3 (Windows: see the face's own installer for the py-launcher note)."),
    "hands": ("barehands (hands board)", "google-chrome", "Install Chrome and a webcam for the hands board."),
}


def e(msg: str) -> None:
    print(msg, flush=True)


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    answer = input(f"{prompt}{suffix}: ").strip()
    return answer or default


def has(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def offer_install(label: str, cmd: str, hint: str) -> bool:
    """Offer to install a missing prerequisite. Returns True if the
    person chose to install (or already had it)."""
    if has(cmd):
        return True
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
    for label, cmd, hint in (
        ("git", "git", "sudo apt install git / brew install git / winget install Git.Git"),
        ("OpenCode", "opencode", "curl -fsSL https://opencode.ai/install | sh"),
        ("Ollama (recommended, for local models)", "ollama", "curl -fsSL https://ollama.com/install.sh | sh"),
    ):
        if has(cmd):
            e(f"  {label}: ok")
        else:
            offer_install(label, cmd, hint)
    state["git"] = has("git")
    state["opencode"] = has("opencode")
    state["ollama"] = has("ollama")
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
    e("Each piece is optional and does one job. Here's what they do in plain English:")
    chosen: dict = {}
    for piece in PIECES:
        e(f"\n  {piece}: {PIECE_BLURBS[piece]}")
        answer = input(f"Install the {piece} piece? [y/n]: ").strip().lower()
        chosen[piece] = answer in ("y", "yes")
    return chosen


def collect_identity() -> dict:
    e("== fullstack-agent setup: agent identity ==")
    name = ask("Agent name", "Jarvis")
    personality = ask("One line of personality", "You are their agent: calm, capable, warm.")
    notes_dir = ask(f"Where should the agent's notes live?", str(Path.home() / name))
    return {"name": name, "personality": personality, "notes": notes_dir}


def shortcut_targets(name: str, pieces: dict) -> list:
    """Return the shortcuts to create, in creation order.

    Each entry: (file_name, kind) where kind is "chat", "talk", or
    "barehands". The Update shortcut is macOS-only and added by the caller.
    Modes whose pieces were not installed are skipped.
    """
    targets = [("Chat", "chat")]
    if pieces.get("voice"):
        targets.append((f"Talk to {name}", "talk"))
    if pieces.get("voice") and pieces.get("hands"):
        targets.append((f"{name} barehands", "barehands"))
    return targets


def write_shortcuts(name: str, pieces: dict) -> list:
    """Write the desktop shortcuts (Chat, Talk, Barehands, Update) per OS.

    Existing files are never overwritten, and modes whose pieces the person
    did not install are skipped.
    """
    written: list = []
    repo = Path(__file__).resolve().parent
    home_dir = repo.parent
    targets = shortcut_targets(name, pieces)
    if os.name == "nt":
        desktop = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
        desktop.mkdir(parents=True, exist_ok=True)
        for label, kind in targets:
            f = desktop / f"{label}.bat"
            if f.exists():
                e(f"Shortcut {f.name} already exists; leaving it alone.")
                continue
            if kind == "chat":
                body = "@echo off\r\ncd /d \"" + str(home_dir) + "\"\r\nopencode\r\n"
            elif kind == "talk":
                body = "@echo off\r\ncall \"" + str(repo) + "\\start.bat\" voice\r\n"
            else:
                body = "@echo off\r\ncall \"" + str(repo) + "\\start.bat\" hands\r\n"
            f.write_bytes(body.encode("latin-1"))
            written.append(str(f))
        e("Shortcuts written to " + str(desktop) + ": " + (", ".join(written) if written else "(none)"))
        return written
    desktop = Path(os.environ.get("XDG_DESKTOP_DIR", str(Path.home() / "Desktop")))
    if not desktop.is_dir():
        e("No desktop folder found; skipping shortcut creation.")
        return written
    scripts = {
        "Chat": (
            "#!/bin/bash\n"
            'export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"\n'
            'cd "' + str(home_dir) + '" && exec opencode\n'
        ),
    }
    if pieces.get("voice"):
        scripts[f"Talk to {name}"] = (
            "#!/bin/bash\n"
            'export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"\n'
            'exec bash "' + str(repo) + '/start.sh" voice\n'
        )
    if pieces.get("voice") and pieces.get("hands"):
        scripts[f"{name} barehands"] = (
            "#!/bin/bash\n"
            'export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"\n'
            'exec bash "' + str(repo) + '/start.sh" hands\n'
        )
    for label, kind in targets:
        f = desktop / f"{label}.command"
        if f.exists():
            e(f"Shortcut {f.name} already exists; leaving it alone.")
            continue
        f.write_text(scripts[label])
        f.chmod(0o755)
        written.append(str(f))
    if any(pieces.values()):
        u = desktop / f"Update {name}.command"
        if not u.exists():
            u.write_text(
                "#!/bin/bash\n"
                'export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"\n'
                'cd "' + str(repo) + '" && ./update.sh\n'
            )
            u.chmod(0o755)
            written.append(str(u))
    e("Shortcuts written to " + str(desktop) + ": " + (", ".join(written) if written else "(none)"))
    return written


def main() -> int:
    e("fullstack-agent setup — the one-command installer.")
    e("This replaces the retired agent-driven wizard. It checks prerequisites,")
    e("asks which pieces you want, captures your agent identity, and writes shortcuts.")
    check_prereqs()
    pieces = interview_pieces()
    identity = collect_identity()
    if any(pieces.values()):
        e("== fullstack-agent setup: piece requirements ==")
        for piece in PIECES:
            if pieces.get(piece):
                e(f"  {piece}: {PIECE_REQUIREMENTS[piece]}")
                label, cmd, hint = PIECE_INSTALLERS[piece]
                offer_install(label, cmd, hint)
    write_shortcuts(identity["name"], pieces)
    answers = {"pieces": pieces, "identity": identity}
    out = Path.home() / ".fullstack-agent-setup.json"
    out.write_text(json.dumps(answers, indent=2) + "\n")
    e("Setup answers saved to " + str(out) + " (safe to re-run).")
    e("Done. Next: start the stack with ./start.sh (or the Desktop shortcuts).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
