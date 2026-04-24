"""
notify — unified desktop notification helper (macOS first-class, Win/Linux via SSH).

Priority order:
  1. terminal-notifier (brew install terminal-notifier, bundle id
     `nl.superalloy.oss.terminal-notifier`; shows as its own entry in
     System Settings → Notifications, permissions are visible & manageable.
     **Strongly recommended** on macOS.)
  2. osascript (fallback; permission ownership falls under launchd/sshd,
     which recent macOS versions restrict tightly.)

Cross-platform behaviour:
  - macOS: invoke terminal-notifier locally.
  - Windows / Linux: forward to a remote Mac over SSH (host configured via
    THROUGHLINE_NOTIFY_SSH_HOST env var; if unset, remote notifications are
    silently disabled).
  - All failures are silent — this helper must never block the caller.

Usage:
    from daemon.notify import notify
    notify("Title", "Body text", sound="Glass", group="flywheel")
"""
import os
import platform
import shutil
import subprocess

# Optional SSH destination for Win/Linux → Mac forwarding.
# Leave unset to disable remote notifications.
MAC_SSH_HOST = os.environ.get("THROUGHLINE_NOTIFY_SSH_HOST", "")

# Default notification group. Overridable per-call.
DEFAULT_GROUP = os.environ.get("THROUGHLINE_NOTIFY_GROUP", "throughline-flywheel")

TN_PATH_CANDIDATES = [
    "/opt/homebrew/bin/terminal-notifier",  # Apple Silicon homebrew
    "/usr/local/bin/terminal-notifier",     # Intel homebrew
]


def _find_local_tn():
    """Locate the terminal-notifier binary on macOS."""
    found = shutil.which("terminal-notifier")
    if found:
        return found
    for p in TN_PATH_CANDIDATES:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None


def _notify_mac_local(title: str, body: str, sound: str, group: str):
    """Run terminal-notifier locally on macOS; fall back to osascript on failure."""
    tn = _find_local_tn()
    if tn:
        args = [tn, "-title", title, "-message", body]
        if sound:
            args += ["-sound", sound]
        if group:
            args += ["-group", group]
        try:
            subprocess.run(args, timeout=5, capture_output=True)
            return True
        except Exception:
            pass
    # Fallback: osascript (permission attribution is murkier, but better than nothing).
    try:
        safe_title = title.replace('"', r"\"")[:100]
        safe_body = body.replace('"', r"\"")[:200]
        osa = f'display notification "{safe_body}" with title "{safe_title}"'
        if sound:
            osa += f' sound name "{sound}"'
        subprocess.run(["osascript", "-e", osa], timeout=5, capture_output=True)
        return True
    except Exception:
        return False


def _notify_mac_remote(title: str, body: str, sound: str, group: str):
    """Forward to terminal-notifier on a remote Mac over SSH (Windows/Linux callers)."""
    if not MAC_SSH_HOST:
        return False
    # Double-quote arguments and escape internal quotes / shell metacharacters.
    safe_title = title.replace('"', r"\"").replace("$", r"\$").replace("`", r"\`")
    safe_body = body.replace('"', r"\"").replace("$", r"\$").replace("`", r"\`")
    remote = f'{TN_PATH_CANDIDATES[0]} -title "{safe_title}" -message "{safe_body}"'
    if sound:
        remote += f" -sound {sound}"
    if group:
        remote += f' -group "{group}"'
    try:
        subprocess.run(
            ["ssh", "-o", "ConnectTimeout=3", "-o", "BatchMode=yes", MAC_SSH_HOST, remote],
            timeout=10, capture_output=True,
        )
        return True
    except Exception:
        return False


def notify(title: str, body: str, sound: str = "Glass", group: str = "") -> None:
    """Send a desktop notification. Silent on failure.

    Args:
        title: notification title (<= 100 chars)
        body:  notification body  (<= 200 chars)
        sound: macOS system sound name (Glass/Funk/Basso/Purr/Ping/...);
               pass an empty string to disable sound.
        group: notification group — newer notifications with the same group
               replace older ones, preventing stacking clutter.
    """
    group = group or DEFAULT_GROUP
    try:
        if platform.system() == "Darwin":
            _notify_mac_local(title, body, sound, group)
        else:
            _notify_mac_remote(title, body, sound, group)
    except Exception:
        pass


if __name__ == "__main__":
    # Self-test entry point.
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    location = _find_local_tn() if platform.system() == "Darwin" else f"remote via ssh ({MAC_SSH_HOST or 'disabled'})"
    notify(
        "notify self-test",
        f"platform={platform.system()} tn={location}",
        sound="Glass",
    )
    print("Notification sent.")
