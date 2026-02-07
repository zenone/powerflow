"""
Command-line interface for Power-Flow.

Business Logic:
- First-run: Check for API keys, prompt if missing
- Setup: Discover databases, let user select, map properties
- Sync: Fetch action items from Pocket, create in Notion with deduplication
- CRITICAL: Never create duplicate entries (check pocket_id before creating)

UX Principles:
- Clear, actionable error messages (no stack traces)
- Plain English explanations
- Progress feedback for long operations
- Exit codes for scripting (0=success, 1=error)
"""

import os
import sys
from typing import Optional

from .config import (
    Config,
    get_pocket_api_key,
    get_notion_api_key,
    validate_env,
    CONFIG_FILE,
)
from .notion import NotionClient
from .pocket import PocketClient
from .sync import SyncEngine


# =============================================================================
# OUTPUT HELPERS
# =============================================================================

def print_error(msg: str) -> None:
    """Print error message with red X."""
    print(f"❌ {msg}", file=sys.stderr)


def print_success(msg: str) -> None:
    """Print success message with green check."""
    print(f"✅ {msg}")


def print_info(msg: str) -> None:
    """Print info message."""
    print(f"ℹ️  {msg}")


def print_warning(msg: str) -> None:
    """Print warning message."""
    print(f"⚠️  {msg}")


def print_step(msg: str, end: str = "... ") -> None:
    """Print a step in progress."""
    print(f"   {msg}", end=end, flush=True)


# =============================================================================
# API KEY MANAGEMENT
# =============================================================================

def get_or_prompt_pocket_key(config: Config) -> Optional[str]:
    """
    Get Pocket API key from config, env, or prompt user.
    
    Priority:
    1. Environment variable (POCKET_API_KEY)
    2. Config file
    3. Interactive prompt
    """
    # Check environment first
    key = os.getenv("POCKET_API_KEY")
    if key:
        return key
    
    # Check config
    if hasattr(config, 'pocket_api_key') and config.pocket_api_key:
        return config.pocket_api_key
    
    # Prompt user
    print()
    print("🔑 Pocket API Key Required")
    print("   Get yours from: Pocket App → Settings → Developers → API Keys → Create Secret Key")
    print()
    try:
        key = input("   Enter your Pocket API key (pk_...): ").strip()
        if key:
            return key
    except (KeyboardInterrupt, EOFError):
        print()
        return None
    
    return None


def get_or_prompt_notion_key(config: Config) -> Optional[str]:
    """
    Get Notion API key from config, env, or prompt user.
    
    Priority:
    1. Environment variable (NOTION_API_KEY)
    2. Config file
    3. Interactive prompt
    """
    # Check environment first
    key = os.getenv("NOTION_API_KEY")
    if key:
        return key
    
    # Check config
    if hasattr(config, 'notion_api_key') and config.notion_api_key:
        return config.notion_api_key
    
    # Prompt user
    print()
    print("🔑 Notion API Key Required")
    print("   Get yours from: notion.so/my-integrations → New Integration")
    print("   Then share your database with the integration")
    print()
    try:
        key = input("   Enter your Notion API key (ntn_... or secret_...): ").strip()
        if key:
            return key
    except (KeyboardInterrupt, EOFError):
        print()
        return None
    
    return None


def verify_pocket_key(key: str) -> tuple[bool, str]:
    """
    Verify Pocket API key works.
    
    Returns:
        (success, error_message)
    """
    try:
        client = PocketClient(key)
        client.get_recordings(limit=1)
        return True, ""
    except Exception as e:
        error = str(e)
        if "401" in error or "Unauthorized" in error:
            return False, "Invalid API key. Please check and try again."
        elif "403" in error or "Forbidden" in error:
            return False, "API key doesn't have permission. Create a key with 'Read' access."
        elif "connection" in error.lower() or "resolve" in error.lower():
            return False, "Can't connect to Pocket API. Check your internet connection."
        else:
            return False, f"API error: {error}"


def verify_notion_key(key: str) -> tuple[bool, str]:
    """
    Verify Notion API key works.
    
    Returns:
        (success, error_message)
    """
    try:
        client = NotionClient(key)
        client.search_databases()
        return True, ""
    except Exception as e:
        error = str(e)
        if "401" in error or "Unauthorized" in error:
            return False, "Invalid API key. Please check and try again."
        elif "403" in error or "Forbidden" in error:
            return False, "API key doesn't have permission. Check your integration settings."
        elif "connection" in error.lower() or "resolve" in error.lower():
            return False, "Can't connect to Notion API. Check your internet connection."
        else:
            return False, f"API error: {error}"


# =============================================================================
# SETUP COMMAND
# =============================================================================

def cmd_setup() -> int:
    """
    Interactive setup wizard.
    
    Business Logic:
    1. Get/prompt for API keys
    2. Verify both keys work
    3. Discover accessible Notion databases
    4. Let user select target database
    5. Analyze schema and create property mapping
    6. Optionally create missing properties
    7. Save configuration
    
    This is idempotent - can be run multiple times safely.
    """
    print("\n🚀 Power-Flow Setup\n")

    config = Config.load()

    # Step 1: Get Pocket API key
    pocket_key = get_or_prompt_pocket_key(config)
    if not pocket_key:
        print_error("Pocket API key is required.")
        print("   Set POCKET_API_KEY environment variable or enter it when prompted.")
        return 1

    # Step 2: Verify Pocket key
    print_step("Checking Pocket API")
    success, error = verify_pocket_key(pocket_key)
    if not success:
        print("❌")
        print_error(error)
        return 1
    print("✓")

    # Step 3: Get Notion API key
    notion_key = get_or_prompt_notion_key(config)
    if not notion_key:
        print_error("Notion API key is required.")
        print("   Set NOTION_API_KEY environment variable or enter it when prompted.")
        return 1

    # Step 4: Verify Notion key
    print_step("Checking Notion API")
    success, error = verify_notion_key(notion_key)
    if not success:
        print("❌")
        print_error(error)
        return 1
    print("✓")

    # Step 5: Discover databases
    print("\n📚 Scanning for accessible databases...\n")
    notion = NotionClient(notion_key)
    
    try:
        databases = notion.search_databases()
    except Exception as e:
        print_error(f"Failed to list databases: {e}")
        return 1

    formatted = notion.format_databases_for_display(databases)

    if not formatted:
        print_error("No databases found!")
        print()
        print("   To fix this:")
        print("   1. Open a Notion database you want to sync to")
        print("   2. Click '...' menu → 'Connections'")
        print("   3. Add your integration (the one you created)")
        print("   4. Re-run this setup")
        return 1

    # Step 6: Display databases and get selection
    print("Found databases:")
    for i, db in enumerate(formatted, 1):
        print(f"  {i}. {db['emoji']} {db['title']}")
    print(f"  {len(formatted) + 1}. [Enter ID manually]")

    # Get user selection
    selected = None
    while selected is None:
        try:
            choice = input(f"\nSelect database [1-{len(formatted) + 1}]: ").strip()
            if not choice:
                continue
                
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(formatted):
                selected = formatted[choice_num - 1]
            elif choice_num == len(formatted) + 1:
                db_id = input("Enter database ID: ").strip()
                if db_id:
                    try:
                        db_info = notion.get_database(db_id)
                        title_parts = db_info.get("title", [])
                        title = title_parts[0].get("plain_text", "Untitled") if title_parts else "Untitled"
                        selected = {"id": db_id, "title": title, "emoji": "📄"}
                    except Exception:
                        print_error("Could not access that database.")
                        print("   Check the ID and make sure your integration has access.")
            else:
                print(f"   Please enter a number between 1 and {len(formatted) + 1}")
        except ValueError:
            print("   Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n\nSetup cancelled.")
            return 1

    print(f"\n✅ Selected: {selected['emoji']} {selected['title']}")

    # Step 7: Analyze schema and create mapping
    print(f"\n📊 Analyzing schema...\n")
    
    try:
        schema = notion.get_database_schema(selected["id"])
    except Exception as e:
        print_error(f"Failed to get database schema: {e}")
        return 1
    
    schema_names = {name: prop.get("type") for name, prop in schema.items()}

    # Build property mapping
    # We need: title, pocket_id (dedup), priority, due_date, context, source
    existing_mappings = []
    to_create = []

    # Title always exists in Notion databases
    existing_mappings.append(("Action Item", "Name", "existing"))

    # Check for Priority (select type)
    if "Priority" in schema_names and schema_names["Priority"] == "select":
        existing_mappings.append(("Priority", "Priority", "existing"))

    # Check for Due Date (date type)
    for name in ["Due Date", "Due", "DueDate"]:
        if name in schema_names and schema_names[name] == "date":
            existing_mappings.append(("Due Date", name, "existing"))
            break

    # Check for pocket_id field (rich_text for deduplication)
    # CRITICAL: This is required for deduplication
    pocket_id_field = None
    for name in ["Inbox ID", "pocket_id", "Pocket ID", "Source ID"]:
        if name in schema_names and schema_names[name] == "rich_text":
            pocket_id_field = name
            existing_mappings.append(("pocket_id", name, "existing"))
            break
    
    if not pocket_id_field:
        # Must create this field - it's required for deduplication
        to_create.append(("pocket_id", "Inbox ID", "rich_text"))

    # Check for context field (rich_text, NOT relation)
    context_field = None
    for name in ["Next step", "Notes", "Description", "Details"]:
        if name in schema_names and schema_names[name] == "rich_text":
            context_field = name
            existing_mappings.append(("Context", name, "existing"))
            break
    
    if not context_field:
        # Context field not found - create it
        to_create.append(("Context", "Action Context", "rich_text"))

    # Check for source URL field
    source_field = None
    for name in ["Source", "URL", "Link", "Recording"]:
        if name in schema_names and schema_names[name] == "url":
            source_field = name
            existing_mappings.append(("Source", name, "existing"))
            break
    
    if not source_field:
        to_create.append(("Source", "Source", "url"))

    # Check for tags field (multi_select)
    tags_field = None
    for name in ["Tags", "Labels", "Categories"]:
        if name in schema_names and schema_names[name] == "multi_select":
            tags_field = name
            existing_mappings.append(("Tags", name, "existing"))
            break
    
    if not tags_field:
        to_create.append(("Tags", "Tags", "multi_select"))

    # Display mapping
    print("Mapping Pocket → Notion:\n")
    for pocket_field, notion_field, _ in existing_mappings:
        print(f"   ✅ {pocket_field:15} → {notion_field}")

    if to_create:
        print()
        for pocket_field, notion_field, _ in to_create:
            print(f"   ➕ {pocket_field:15} → {notion_field} [will create]")

    # Step 8: Confirm and create properties
    if to_create:
        print()
        try:
            confirm = input("Create missing properties? [Y/n]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n\nSetup cancelled.")
            return 1
            
        if confirm and confirm not in ["y", "yes", ""]:
            print("\nSetup cancelled. Missing properties are required for sync.")
            print("Run setup again when ready.")
            return 1

        # Create properties
        print()
        for _, prop_name, prop_type in to_create:
            print_step(f"Creating {prop_name}")
            try:
                notion.create_property(selected["id"], prop_name, prop_type)
                print("✓")
            except Exception as e:
                print("❌")
                print_error(f"Failed to create property: {e}")
                return 1

    # Step 9: Build and save configuration
    property_map = {"title": "Name"}
    
    # Add mappings from existing
    field_mapping = {
        "Priority": "priority",
        "Due Date": "due_date",
        "pocket_id": "pocket_id",
        "Context": "context",
        "Source": "source_url",
        "Tags": "tags",
    }
    
    for pocket_field, notion_field, _ in existing_mappings:
        if pocket_field in field_mapping:
            property_map[field_mapping[pocket_field]] = notion_field
    
    # Add mappings from created
    for pocket_field, notion_field, _ in to_create:
        if pocket_field in field_mapping:
            property_map[field_mapping[pocket_field]] = notion_field

    # Ensure pocket_id is always mapped (CRITICAL for dedup)
    if "pocket_id" not in property_map:
        property_map["pocket_id"] = to_create[0][1] if to_create else "Inbox ID"

    # Save configuration
    config.notion.database_id = selected["id"]
    config.notion.database_name = selected["title"]
    config.notion.property_map = property_map
    config.save()

    print(f"\n✅ Config saved: {CONFIG_FILE}")
    print(f"\n🎉 Setup complete! Run 'powerflow sync' to start syncing.\n")

    return 0


# =============================================================================
# SYNC COMMAND
# =============================================================================

def cmd_sync(dry_run: bool = False) -> int:
    """
    Sync action items from Pocket to Notion.
    
    Business Logic:
    1. Load configuration
    2. Verify API keys are available
    3. Fetch action items from Pocket
    4. For each item:
       a. Check if pocket_id already exists in Notion (DEDUPLICATION)
       b. If exists → skip
       c. If not exists → create
    5. Report results
    
    CRITICAL: Never create duplicates. Always check before creating.
    """
    # Get API keys
    pocket_key = os.getenv("POCKET_API_KEY")
    notion_key = os.getenv("NOTION_API_KEY")
    
    if not pocket_key:
        print_error("Pocket API key not found.")
        print("   Set POCKET_API_KEY environment variable.")
        return 1
    
    if not notion_key:
        print_error("Notion API key not found.")
        print("   Set NOTION_API_KEY environment variable.")
        return 1

    # Load config
    config = Config.load()
    if not config.is_configured:
        print_error("Not configured yet.")
        print("   Run 'powerflow setup' first to select a Notion database.")
        return 1

    # Initialize clients
    try:
        pocket = PocketClient(pocket_key)
        notion = NotionClient(notion_key)
    except Exception as e:
        print_error(f"Failed to initialize API clients: {e}")
        return 1

    engine = SyncEngine(pocket, notion, config)

    # Run sync
    mode = "[DRY RUN] " if dry_run else ""
    print(f"\n🔄 {mode}Syncing Pocket → Notion ({config.notion.database_name})...\n")

    try:
        result = engine.sync(dry_run=dry_run)
    except Exception as e:
        print_error(f"Sync failed: {e}")
        return 1

    # Report results
    if result.created:
        print_success(f"Created {result.created} new items")
    if result.skipped:
        print_info(f"Skipped {result.skipped} existing items")
    if result.failed:
        print_error(f"Failed: {result.failed} items")
        for err in result.errors[:5]:
            print(f"   • {err}")
        if len(result.errors) > 5:
            print(f"   ... and {len(result.errors) - 5} more errors")

    if result.total == 0:
        print_info("No action items found in Pocket")

    print()
    return 0 if result.failed == 0 else 1


# =============================================================================
# STATUS COMMAND
# =============================================================================

def cmd_status() -> int:
    """Show sync status and pending item count."""
    config = Config.load()

    print("\n📊 Power-Flow Status\n")

    if not config.is_configured:
        print_warning("Not configured.")
        print("   Run 'powerflow setup' to get started.")
        return 0

    print(f"   Database:  {config.notion.database_name}")
    print(f"   Last sync: {config.pocket.last_sync or 'Never'}")
    print(f"   Config:    {CONFIG_FILE}")

    # Check API keys
    pocket_key = os.getenv("POCKET_API_KEY")
    notion_key = os.getenv("NOTION_API_KEY")

    if not pocket_key or not notion_key:
        print()
        if not pocket_key:
            print_warning("POCKET_API_KEY not set")
        if not notion_key:
            print_warning("NOTION_API_KEY not set")
        return 0

    # Try to get pending count
    print("\n   Checking for new items...", end=" ", flush=True)
    try:
        pocket = PocketClient(pocket_key)
        notion = NotionClient(notion_key)
        engine = SyncEngine(pocket, notion, config)
        pending = engine.get_pending_count()
        print(f"\n\n📬 {pending} new items ready to sync")
    except Exception as e:
        print(f"\n\n⚠️  Could not check: {e}")

    print()
    return 0


# =============================================================================
# CONFIG COMMAND
# =============================================================================

def cmd_config(action: str = "show") -> int:
    """Manage configuration."""
    config = Config.load()

    if action == "show":
        print("\n⚙️  Power-Flow Configuration\n")

        if not config.is_configured:
            print_warning("Not configured.")
            print("   Run 'powerflow setup' to get started.")
            return 0

        print(f"   Database ID:   {config.notion.database_id}")
        print(f"   Database Name: {config.notion.database_name}")
        print(f"   Created:       {config.created_at}")
        print(f"   Last Sync:     {config.pocket.last_sync or 'Never'}")
        print(f"\n   Property Mapping:")
        for pocket, notion in config.notion.property_map.items():
            print(f"      {pocket} → {notion}")
        print(f"\n   Config file: {CONFIG_FILE}")
        print()
        return 0

    elif action == "reset":
        if not CONFIG_FILE.exists():
            print_info("No configuration to reset.")
            return 0
        
        try:
            confirm = input("Reset all configuration? This cannot be undone. [y/N]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            return 1
            
        if confirm == "y":
            CONFIG_FILE.unlink()
            print_success("Configuration reset.")
            print("   Run 'powerflow setup' to configure again.")
        else:
            print("Cancelled.")
        return 0

    else:
        print_error(f"Unknown config action: {action}")
        print("   Use: powerflow config show")
        print("        powerflow config reset")
        return 1


# =============================================================================
# DAEMON COMMAND
# =============================================================================

def cmd_daemon(args: list[str]) -> int:
    """
    Manage background sync daemon.
    
    Subcommands:
    - start [--interval Xm] [--foreground]: Start daemon
    - stop: Stop daemon
    - status: Show daemon status
    - install [--interval Xm]: Install as system service
    - uninstall: Remove system service
    """
    from . import daemon
    
    if not args:
        print_error("Missing daemon subcommand")
        print("   Use: powerflow daemon start|stop|status|install|uninstall")
        return 1
    
    subcommand = args[0].lower()
    
    # Parse --interval flag
    interval = daemon.DEFAULT_INTERVAL_MINUTES
    for i, arg in enumerate(args):
        if arg == "--interval" and i + 1 < len(args):
            try:
                interval = daemon.parse_interval(args[i + 1])
            except ValueError:
                print_error(f"Invalid interval: {args[i + 1]}")
                print("   Examples: 5m, 15m, 30m, 1h")
                return 1
    
    foreground = "--foreground" in args or "-f" in args
    
    if subcommand == "start":
        return daemon.start_daemon(interval, foreground=foreground)
    elif subcommand == "stop":
        return daemon.stop_daemon()
    elif subcommand == "status":
        return daemon.daemon_status()
    elif subcommand == "install":
        return daemon.install_service(interval)
    elif subcommand == "uninstall":
        return daemon.uninstall_service()
    else:
        print_error(f"Unknown daemon subcommand: {subcommand}")
        print("   Use: powerflow daemon start|stop|status|install|uninstall")
        return 1


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main(args: Optional[list[str]] = None) -> int:
    """Main entry point."""
    if args is None:
        args = sys.argv[1:]

    if not args:
        print_usage()
        return 0

    command = args[0].lower()

    try:
        if command == "setup":
            return cmd_setup()
        elif command == "sync":
            dry_run = "--dry-run" in args or "-n" in args
            return cmd_sync(dry_run=dry_run)
        elif command == "status":
            return cmd_status()
        elif command == "config":
            action = args[1] if len(args) > 1 else "show"
            return cmd_config(action)
        elif command == "daemon":
            return cmd_daemon(args[1:])
        elif command in ["--help", "-h", "help"]:
            print_usage()
            return 0
        elif command in ["--version", "-v"]:
            from . import __version__
            print(f"powerflow {__version__}")
            return 0
        else:
            print_error(f"Unknown command: {command}")
            print_usage()
            return 1
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        print("   If this persists, please report it at:")
        print("   https://github.com/zenone/powerflow/issues")
        return 1


def print_usage():
    """Print usage information."""
    print("""
Power-Flow: Sync Pocket AI action items to Notion

Usage:
  powerflow setup              Configure database and property mapping
  powerflow sync               Sync action items to Notion
  powerflow sync --dry-run     Preview sync without making changes
  powerflow status             Show sync status and pending count
  powerflow config show        Show current configuration
  powerflow config reset       Reset all configuration

Automatic Sync:
  powerflow daemon start             Start background sync (every 15 min)
  powerflow daemon start --interval 5m   Custom interval (5m, 15m, 1h)
  powerflow daemon stop              Stop background sync
  powerflow daemon status            Check if daemon is running
  powerflow daemon install           Install as system service (auto-start on boot)
  powerflow daemon uninstall         Remove system service

Options:
  -h, --help     Show this help
  -v, --version  Show version

Environment:
  POCKET_API_KEY   Your Pocket AI API key (pk_...)
  NOTION_API_KEY   Your Notion integration token (ntn_... or secret_...)

First time? Run 'powerflow setup' to get started.
""")


if __name__ == "__main__":
    sys.exit(main())
