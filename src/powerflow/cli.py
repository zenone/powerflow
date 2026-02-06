"""Command-line interface for Power-Flow."""

import sys
from typing import Optional

from .config import Config, get_pocket_api_key, get_notion_api_key, validate_env
from .notion import NotionClient
from .pocket import PocketClient
from .sync import SyncEngine


def print_error(msg: str) -> None:
    """Print error message."""
    print(f"❌ {msg}", file=sys.stderr)


def print_success(msg: str) -> None:
    """Print success message."""
    print(f"✅ {msg}")


def print_info(msg: str) -> None:
    """Print info message."""
    print(f"ℹ️  {msg}")


def print_warning(msg: str) -> None:
    """Print warning message."""
    print(f"⚠️  {msg}")


def cmd_setup() -> int:
    """Interactive setup wizard."""
    print("\n🚀 Power-Flow Setup\n")

    # Check environment
    missing = validate_env()
    if missing:
        print_error(f"Missing environment variables: {', '.join(missing)}")
        print("\nSet them in your environment or .env file:")
        print("  export POCKET_API_KEY=pk_xxx")
        print("  export NOTION_API_KEY=ntn_xxx")
        return 1

    # Test Pocket API
    print("🔑 Checking Pocket API...", end=" ", flush=True)
    pocket = PocketClient(get_pocket_api_key())
    if not pocket.test_connection():
        print("❌")
        print_error("Could not connect to Pocket API. Check your API key.")
        return 1
    print("✓")

    # Test Notion API
    print("🔑 Checking Notion API...", end=" ", flush=True)
    notion = NotionClient(get_notion_api_key())
    if not notion.test_connection():
        print("❌")
        print_error("Could not connect to Notion API. Check your API key.")
        return 1
    print("✓")

    # Discover databases
    print("\n📚 Scanning for accessible databases...\n")
    databases = notion.search_databases()
    formatted = notion.format_databases_for_display(databases)

    if not formatted:
        print_error("No databases found!")
        print("\nMake sure you've shared at least one database with your integration:")
        print("  1. Open a Notion database")
        print("  2. Click '...' menu → 'Connections'")
        print("  3. Add your integration")
        return 1

    # Display databases
    print("Found databases:")
    for i, db in enumerate(formatted, 1):
        print(f"  {i}. {db['emoji']} {db['title']}")
    print(f"  {len(formatted) + 1}. [Enter ID manually]")

    # Get selection
    while True:
        try:
            choice = input(f"\nSelect database [1-{len(formatted) + 1}]: ").strip()
            choice_num = int(choice)
            if 1 <= choice_num <= len(formatted):
                selected = formatted[choice_num - 1]
                break
            elif choice_num == len(formatted) + 1:
                db_id = input("Enter database ID: ").strip()
                if db_id:
                    # Validate the ID
                    try:
                        db_info = notion.get_database(db_id)
                        title_parts = db_info.get("title", [])
                        title = title_parts[0].get("plain_text", "Untitled") if title_parts else "Untitled"
                        selected = {"id": db_id, "title": title, "emoji": "📄"}
                        break
                    except Exception:
                        print_error("Could not access that database. Check the ID and permissions.")
                else:
                    print("Please enter a database ID.")
            else:
                print(f"Please enter a number between 1 and {len(formatted) + 1}")
        except ValueError:
            print("Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n\nSetup cancelled.")
            return 1

    print(f"\n✅ Selected: {selected['emoji']} {selected['title']}")

    # Analyze schema and show mapping
    print(f"\n📊 Analyzing schema...\n")
    schema = notion.get_database_schema(selected["id"])
    schema_names = set(schema.keys())

    # Define what we need
    required_props = {
        "Inbox ID": "rich_text",  # For pocket_id / dedup
    }
    optional_props = {
        "Context": "rich_text",
        "Source": "url",
    }

    # Check what exists and what needs creating
    existing_mappings = []
    to_create = []

    # Title always exists
    existing_mappings.append(("Action Item", "Name", "existing"))

    # Check Priority
    if "Priority" in schema_names:
        existing_mappings.append(("Priority", "Priority", "existing"))

    # Check Due Date
    for name in ["Due Date", "Due", "DueDate"]:
        if name in schema_names:
            existing_mappings.append(("Due Date", name, "existing"))
            break

    # Check Inbox ID (for dedup)
    if "Inbox ID" in schema_names:
        existing_mappings.append(("pocket_id", "Inbox ID", "existing"))
    else:
        to_create.append(("pocket_id", "Inbox ID", "rich_text"))

    # Check optional properties
    for prop_name, prop_type in optional_props.items():
        if prop_name in schema_names:
            existing_mappings.append((prop_name, prop_name, "existing"))
        else:
            to_create.append((prop_name, prop_name, prop_type))

    # Display mapping
    print("Mapping Pocket → Notion:\n")
    for pocket_field, notion_field, status in existing_mappings:
        print(f"   ✅ {pocket_field:15} → {notion_field}")

    if to_create:
        print()
        for pocket_field, notion_field, prop_type in to_create:
            print(f"   ➕ {pocket_field:15} → {notion_field} [will create]")

    # Confirm
    if to_create:
        print()
        confirm = input("Create missing properties? [Y/n]: ").strip().lower()
        if confirm and confirm != "y":
            print("\nSetup cancelled. You can re-run setup anytime.")
            return 1

        # Create properties
        print()
        for _, prop_name, prop_type in to_create:
            print(f"   Creating {prop_name}...", end=" ", flush=True)
            try:
                notion.create_property(selected["id"], prop_name, prop_type)
                print("✓")
            except Exception as e:
                print("❌")
                print_error(f"Failed to create property: {e}")
                return 1

    # Build property map
    property_map = {
        "title": "Name",
        "pocket_id": "Inbox ID",
    }

    # Add existing mappings
    for pocket_field, notion_field, _ in existing_mappings:
        if pocket_field == "Priority":
            property_map["priority"] = notion_field
        elif pocket_field == "Due Date":
            property_map["due_date"] = notion_field
        elif pocket_field == "Context":
            property_map["context"] = notion_field
        elif pocket_field == "Source":
            property_map["source_url"] = notion_field

    # Add created mappings
    for pocket_field, notion_field, _ in to_create:
        if pocket_field == "Context":
            property_map["context"] = notion_field
        elif pocket_field == "Source":
            property_map["source_url"] = notion_field

    # Save config
    config = Config()
    config.notion.database_id = selected["id"]
    config.notion.database_name = selected["title"]
    config.notion.property_map = property_map
    config.save()

    print(f"\n✅ Config saved: ~/.powerflow/config.json")
    print(f"\n🎉 Setup complete! Run 'powerflow sync' to start syncing.\n")

    return 0


def cmd_sync(dry_run: bool = False) -> int:
    """Sync action items from Pocket to Notion."""
    missing = validate_env()
    if missing:
        print_error(f"Missing environment variables: {', '.join(missing)}")
        return 1

    config = Config.load()
    if not config.is_configured:
        print_error("Not configured. Run 'powerflow setup' first.")
        return 1

    pocket = PocketClient(get_pocket_api_key())
    notion = NotionClient(get_notion_api_key())
    engine = SyncEngine(pocket, notion, config)

    mode = "[DRY RUN] " if dry_run else ""
    print(f"\n🔄 {mode}Syncing Pocket → Notion ({config.notion.database_name})...\n")

    result = engine.sync(dry_run=dry_run)

    # Print results
    if result.created:
        print_success(f"Created {result.created} new items")
    if result.skipped:
        print_info(f"Skipped {result.skipped} existing items")
    if result.failed:
        print_error(f"Failed: {result.failed} items")
        for err in result.errors[:5]:  # Show first 5 errors
            print(f"   • {err}")
        if len(result.errors) > 5:
            print(f"   ... and {len(result.errors) - 5} more errors")

    if result.total == 0:
        print_info("No action items found in Pocket")

    print()
    return 0 if result.failed == 0 else 1


def cmd_status() -> int:
    """Show sync status."""
    config = Config.load()

    print("\n📊 Power-Flow Status\n")

    if not config.is_configured:
        print_warning("Not configured. Run 'powerflow setup' first.")
        return 0

    print(f"Database: {config.notion.database_name}")
    print(f"Last sync: {config.pocket.last_sync or 'Never'}")

    # Check env
    missing = validate_env()
    if missing:
        print_warning(f"Missing env vars: {', '.join(missing)}")
        return 0

    # Get pending count
    pocket = PocketClient(get_pocket_api_key())
    notion = NotionClient(get_notion_api_key())
    engine = SyncEngine(pocket, notion, config)

    print("\nChecking for pending items...", end=" ", flush=True)
    try:
        pending = engine.get_pending_count()
        print(f"\n\n📬 {pending} items ready to sync")
    except Exception as e:
        print(f"\n\n⚠️  Could not check: {e}")

    print()
    return 0


def cmd_config() -> int:
    """Show current configuration."""
    config = Config.load()

    print("\n⚙️  Power-Flow Configuration\n")

    if not config.is_configured:
        print_warning("Not configured. Run 'powerflow setup' first.")
        return 0

    print(f"Database ID: {config.notion.database_id}")
    print(f"Database Name: {config.notion.database_name}")
    print(f"Created: {config.created_at}")
    print(f"Last Sync: {config.pocket.last_sync or 'Never'}")
    print(f"\nProperty Mapping:")
    for pocket, notion in config.notion.property_map.items():
        print(f"  {pocket} → {notion}")

    print(f"\nConfig file: ~/.powerflow/config.json")
    print()
    return 0


def main(args: Optional[list[str]] = None) -> int:
    """Main entry point."""
    if args is None:
        args = sys.argv[1:]

    if not args:
        print_usage()
        return 0

    command = args[0].lower()

    if command == "setup":
        return cmd_setup()
    elif command == "sync":
        dry_run = "--dry-run" in args or "-n" in args
        return cmd_sync(dry_run=dry_run)
    elif command == "status":
        return cmd_status()
    elif command == "config":
        return cmd_config()
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


def print_usage():
    """Print usage information."""
    print("""
Power-Flow: Sync Pocket AI to Notion

Usage:
  powerflow setup           Configure Notion database and mapping
  powerflow sync            Sync action items to Notion
  powerflow sync --dry-run  Preview sync without making changes
  powerflow status          Show sync status and pending items
  powerflow config          Show current configuration

Options:
  -h, --help     Show this help
  -v, --version  Show version

Environment:
  POCKET_API_KEY   Your Pocket AI API key
  NOTION_API_KEY   Your Notion integration token
""")


if __name__ == "__main__":
    sys.exit(main())
