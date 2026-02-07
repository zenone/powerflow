"""
Background daemon for automatic Power-Flow sync.

Features:
- Configurable sync interval (default: 15 minutes)
- PID file to prevent duplicate instances
- Graceful shutdown on SIGTERM/SIGINT
- Logging to file
- launchd/systemd service installation
"""

import os
import sys
import signal
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import json

from .config import Config, CONFIG_DIR
from .pocket import PocketClient
from .notion import NotionClient
from .sync import SyncEngine


# Daemon files
PID_FILE = CONFIG_DIR / "daemon.pid"
LOG_FILE = CONFIG_DIR / "daemon.log"
STATE_FILE = CONFIG_DIR / "daemon_state.json"

# Default interval
DEFAULT_INTERVAL_MINUTES = 15
RETRY_DELAY_SECONDS = 60  # Retry failed syncs after 1 minute
MAX_RETRIES = 2


def parse_interval(interval_str: str) -> int:
    """
    Parse interval string to minutes.
    
    Examples: "5m", "15m", "1h", "30"
    """
    interval_str = interval_str.strip().lower()
    
    if interval_str.endswith("h"):
        return int(interval_str[:-1]) * 60
    elif interval_str.endswith("m"):
        return int(interval_str[:-1])
    else:
        # Assume minutes if no suffix
        return int(interval_str)


def setup_logging() -> logging.Logger:
    """Set up daemon logging."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("powerflow-daemon")
    logger.setLevel(logging.INFO)
    
    # File handler with rotation-friendly format
    handler = logging.FileHandler(LOG_FILE)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(handler)
    
    return logger


def save_state(state: dict) -> None:
    """Save daemon state to file."""
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))


def load_state() -> dict:
    """Load daemon state from file."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def send_notification(title: str, message: str) -> None:
    """
    Send a desktop notification (macOS).
    
    Fails silently on other platforms or if notification fails.
    """
    if sys.platform != "darwin":
        return
    
    try:
        import subprocess
        script = f'display notification "{message}" with title "{title}"'
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            timeout=5
        )
    except Exception:
        pass  # Notifications are best-effort


def is_running() -> tuple[bool, Optional[int]]:
    """
    Check if daemon is already running.
    
    Returns:
        (is_running, pid)
    """
    if not PID_FILE.exists():
        return False, None
    
    try:
        pid = int(PID_FILE.read_text().strip())
        # Check if process exists
        os.kill(pid, 0)
        return True, pid
    except (ValueError, ProcessLookupError, PermissionError):
        # PID file exists but process doesn't - stale PID file
        PID_FILE.unlink(missing_ok=True)
        return False, None


def write_pid() -> None:
    """Write current PID to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))


def remove_pid() -> None:
    """Remove PID file."""
    PID_FILE.unlink(missing_ok=True)


class PowerFlowDaemon:
    """Background sync daemon."""
    
    def __init__(self, interval_minutes: int = DEFAULT_INTERVAL_MINUTES):
        self.interval_minutes = interval_minutes
        self.running = False
        self.logger = setup_logging()
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signal gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def _do_sync(self) -> dict:
        """
        Perform a single sync operation.
        
        Returns:
            Result dict with created, skipped, failed counts
        """
        pocket_key = os.getenv("POCKET_API_KEY")
        notion_key = os.getenv("NOTION_API_KEY")
        
        if not pocket_key or not notion_key:
            return {"error": "API keys not set"}
        
        config = Config.load()
        if not config.is_configured:
            return {"error": "Not configured"}
        
        try:
            pocket = PocketClient(pocket_key)
            notion = NotionClient(notion_key)
            engine = SyncEngine(pocket, notion, config)
            
            result = engine.sync()
            
            return {
                "created": result.created,
                "skipped": result.skipped,
                "failed": result.failed,
                "errors": result.errors[:3] if result.errors else [],
            }
        except Exception as e:
            return {"error": str(e)}
    
    def run(self) -> None:
        """Main daemon loop."""
        write_pid()
        self.running = True
        
        self.logger.info(f"Daemon started (PID: {os.getpid()}, interval: {self.interval_minutes}m)")
        
        # Update state
        save_state({
            "status": "running",
            "pid": os.getpid(),
            "interval_minutes": self.interval_minutes,
            "started_at": datetime.now().isoformat(),
            "last_sync": None,
            "last_result": None,
        })
        
        # Send startup notification
        send_notification(
            "Power-Flow Started",
            f"Syncing every {self.interval_minutes} minutes"
        )
        
        consecutive_failures = 0
        
        try:
            while self.running:
                # Perform sync with retry logic
                self.logger.info("Starting sync...")
                start_time = time.time()
                result = self._do_sync()
                duration = time.time() - start_time
                
                # Handle result
                if "error" in result:
                    consecutive_failures += 1
                    self.logger.error(f"Sync failed: {result['error']}")
                    
                    # Retry logic: if failed, retry sooner (up to MAX_RETRIES)
                    if consecutive_failures <= MAX_RETRIES:
                        self.logger.info(f"Will retry in {RETRY_DELAY_SECONDS}s (attempt {consecutive_failures}/{MAX_RETRIES})")
                        wait_seconds = RETRY_DELAY_SECONDS
                    else:
                        self.logger.warning(f"Max retries reached, waiting for next interval")
                        wait_seconds = self.interval_minutes * 60
                        # Notify on persistent failure
                        send_notification(
                            "Power-Flow Sync Failed",
                            f"Check logs: {LOG_FILE}"
                        )
                else:
                    consecutive_failures = 0  # Reset on success
                    self.logger.info(
                        f"Sync complete in {duration:.1f}s: "
                        f"created={result['created']}, "
                        f"skipped={result['skipped']}, "
                        f"failed={result['failed']}"
                    )
                    
                    # Notify on new items (only if something was created)
                    if result.get("created", 0) > 0:
                        send_notification(
                            "Power-Flow Synced",
                            f"{result['created']} new items added to Notion"
                        )
                    
                    wait_seconds = self.interval_minutes * 60
                
                # Update state
                state = load_state()
                state["last_sync"] = datetime.now().isoformat()
                state["last_result"] = result
                state["consecutive_failures"] = consecutive_failures
                state["next_sync"] = (datetime.now() + timedelta(seconds=wait_seconds)).isoformat()
                save_state(state)
                
                # Wait for next interval (check every 10s for shutdown signal)
                waited = 0
                while waited < wait_seconds and self.running:
                    time.sleep(min(10, wait_seconds - waited))
                    waited += 10
        
        finally:
            # Cleanup
            remove_pid()
            save_state({
                "status": "stopped",
                "stopped_at": datetime.now().isoformat(),
            })
            self.logger.info("Daemon stopped")


def start_daemon(interval_minutes: int = DEFAULT_INTERVAL_MINUTES, foreground: bool = False) -> int:
    """
    Start the daemon.
    
    Args:
        interval_minutes: Sync interval
        foreground: Run in foreground (don't daemonize)
    
    Returns:
        Exit code (0 = success)
    """
    running, pid = is_running()
    if running:
        print(f"❌ Daemon already running (PID: {pid})")
        print("   Use 'powerflow daemon stop' first")
        return 1
    
    if foreground:
        # Run in foreground
        print(f"🔄 Starting daemon (interval: {interval_minutes}m)...")
        print("   Press Ctrl+C to stop")
        daemon = PowerFlowDaemon(interval_minutes)
        daemon.run()
        return 0
    
    # Fork to background
    try:
        pid = os.fork()
        if pid > 0:
            # Parent process
            print(f"✅ Daemon started (PID: {pid}, interval: {interval_minutes}m)")
            print(f"   Logs: {LOG_FILE}")
            print("   Use 'powerflow daemon status' to check")
            return 0
    except OSError as e:
        print(f"❌ Failed to fork: {e}")
        return 1
    
    # Child process - become daemon
    os.setsid()
    os.umask(0)
    
    # Redirect stdout/stderr to log
    sys.stdout.flush()
    sys.stderr.flush()
    
    with open(LOG_FILE, 'a') as log:
        os.dup2(log.fileno(), sys.stdout.fileno())
        os.dup2(log.fileno(), sys.stderr.fileno())
    
    # Run daemon
    daemon = PowerFlowDaemon(interval_minutes)
    daemon.run()
    return 0


def stop_daemon() -> int:
    """
    Stop the daemon.
    
    Returns:
        Exit code (0 = success)
    """
    running, pid = is_running()
    if not running:
        print("ℹ️  Daemon is not running")
        return 0
    
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"✅ Sent stop signal to daemon (PID: {pid})")
        
        # Wait for it to stop
        for _ in range(10):
            time.sleep(0.5)
            if not is_running()[0]:
                print("   Daemon stopped")
                return 0
        
        print("⚠️  Daemon still running, sending SIGKILL...")
        os.kill(pid, signal.SIGKILL)
        time.sleep(0.5)
        remove_pid()
        print("   Daemon killed")
        return 0
        
    except ProcessLookupError:
        print("ℹ️  Daemon already stopped")
        remove_pid()
        return 0
    except PermissionError:
        print(f"❌ Permission denied. Try: sudo kill {pid}")
        return 1


def daemon_status() -> int:
    """
    Show daemon status.
    
    Returns:
        Exit code (0 = running, 1 = not running)
    """
    running, pid = is_running()
    state = load_state()
    
    print("\n📊 Power-Flow Daemon Status\n")
    
    if running:
        print(f"   Status:    🟢 Running (PID: {pid})")
    else:
        print("   Status:    ⚪ Stopped")
    
    if state.get("interval_minutes"):
        print(f"   Interval:  {state['interval_minutes']} minutes")
    
    if state.get("started_at"):
        print(f"   Started:   {state['started_at']}")
    
    if state.get("last_sync"):
        print(f"   Last sync: {state['last_sync']}")
        
        result = state.get("last_result", {})
        if "error" in result:
            print(f"   Result:    ❌ {result['error']}")
        elif result:
            print(f"   Result:    ✅ {result.get('created', 0)} created, {result.get('skipped', 0)} skipped")
    
    if running and state.get("next_sync"):
        print(f"   Next sync: {state['next_sync']}")
    
    print(f"\n   Log file:  {LOG_FILE}")
    print()
    
    return 0 if running else 1


def generate_launchd_plist(interval_minutes: int = DEFAULT_INTERVAL_MINUTES) -> str:
    """Generate macOS launchd plist content."""
    # Get the powerflow executable path
    import shutil
    powerflow_path = shutil.which("powerflow") or "/usr/local/bin/powerflow"
    
    # Get API keys from environment (launchd doesn't inherit shell env)
    POCKET_API_KEY = os.getenv("POCKET_API_KEY", "")
    NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.powerflow.sync</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>{powerflow_path}</string>
        <string>sync</string>
    </array>
    
    <key>StartInterval</key>
    <integer>{interval_minutes * 60}</integer>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>{LOG_FILE}</string>
    
    <key>StandardErrorPath</key>
    <string>{LOG_FILE}</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
        <key>POCKET_API_KEY</key>
        <string>{POCKET_API_KEY}</string>
        <key>NOTION_API_KEY</key>
        <string>{NOTION_API_KEY}</string>
    </dict>
</dict>
</plist>
"""


def install_service(interval_minutes: int = DEFAULT_INTERVAL_MINUTES) -> int:
    """
    Install as system service.
    
    Returns:
        Exit code (0 = success)
    """
    if sys.platform != "darwin":
        print("❌ Service installation currently only supports macOS (launchd)")
        print("   For Linux, create a systemd service manually")
        return 1
    
    plist_path = Path.home() / "Library/LaunchAgents/com.powerflow.sync.plist"
    
    # Check if already installed
    if plist_path.exists():
        print(f"⚠️  Service already installed at {plist_path}")
        try:
            confirm = input("   Reinstall? [y/N]: ").strip().lower()
            if confirm != "y":
                return 0
        except (KeyboardInterrupt, EOFError):
            print()
            return 1
    
    # Check for API keys
    if not os.getenv("POCKET_API_KEY") or not os.getenv("NOTION_API_KEY"):
        print("⚠️  API keys not found in environment")
        print("   The service needs API keys. Add them to your shell profile:")
        print()
        print("   export POCKET_API_KEY='pk_...'")
        print("   export NOTION_API_KEY='ntn_...'")
        print()
        try:
            confirm = input("   Continue anyway? [y/N]: ").strip().lower()
            if confirm != "y":
                return 1
        except (KeyboardInterrupt, EOFError):
            print()
            return 1
    
    # Generate and write plist
    plist_content = generate_launchd_plist(interval_minutes)
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_text(plist_content)
    
    print(f"✅ Created {plist_path}")
    
    # Load the service
    import subprocess
    try:
        subprocess.run(["launchctl", "unload", str(plist_path)], 
                      capture_output=True)  # Ignore errors if not loaded
        subprocess.run(["launchctl", "load", str(plist_path)], check=True)
        print(f"✅ Service loaded (syncs every {interval_minutes} minutes)")
        print()
        print("   To stop:    launchctl unload ~/Library/LaunchAgents/com.powerflow.sync.plist")
        print("   To start:   launchctl load ~/Library/LaunchAgents/com.powerflow.sync.plist")
        print(f"   Logs:       {LOG_FILE}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to load service: {e}")
        print(f"   Try manually: launchctl load {plist_path}")
        return 1
    
    return 0


def uninstall_service() -> int:
    """
    Uninstall system service.
    
    Returns:
        Exit code (0 = success)
    """
    if sys.platform != "darwin":
        print("❌ Service uninstallation currently only supports macOS")
        return 1
    
    plist_path = Path.home() / "Library/LaunchAgents/com.powerflow.sync.plist"
    
    if not plist_path.exists():
        print("ℹ️  Service not installed")
        return 0
    
    import subprocess
    try:
        subprocess.run(["launchctl", "unload", str(plist_path)], check=True)
        plist_path.unlink()
        print("✅ Service uninstalled")
    except subprocess.CalledProcessError:
        # May already be unloaded
        plist_path.unlink(missing_ok=True)
        print("✅ Service removed")
    
    return 0
