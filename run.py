#!/usr/bin/env python3
"""
Odoo MCP Server Launcher
Interactive menu to choose transport mode
"""

import sys
import subprocess
from pathlib import Path


def print_banner():
    """Print majestic ASCII art banner"""
    banner = r"""
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║     ██████╗ ██████╗  ██████╗  ██████╗     ███╗   ███╗ ██████╗██████╗     ║
    ║    ██╔═══██╗██╔══██╗██╔═══██╗██╔═══██╗    ████╗ ████║██╔════╝██╔══██╗    ║
    ║    ██║   ██║██║  ██║██║   ██║██║   ██║    ██╔████╔██║██║     ██████╔╝    ║
    ║    ██║   ██║██║  ██║██║   ██║██║   ██║    ██║╚██╔╝██║██║     ██╔═══╝     ║
    ║    ╚██████╔╝██████╔╝╚██████╔╝╚██████╔╝    ██║ ╚═╝ ██║╚██████╗██║         ║
    ║     ╚═════╝ ╚═════╝  ╚═════╝  ╚═════╝     ╚═╝     ╚═╝ ╚═════╝╚═╝         ║
    ║                                                                           ║
    ║                       Model Context Protocol Server                      ║
    ║                                                                           ║
    ║              Two tools. Infinite possibilities. Full API access.         ║
    ║                                                                           ║
    ╚═══════════════════════════════════════════════════════════════════════════╝

                                v1.0.0-beta
    """
    print(banner)


def print_menu():
    """Print transport selection menu"""
    menu = """
    ┌─────────────────────────────────────────────────────────────────┐
    │                     Select Transport Mode                       │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                 │
    │  [1] STDIO Transport (Claude Desktop)                          │
    │      → Process pipes (stdin/stdout)                            │
    │      → No network required                                     │
    │      → Default for Claude Desktop integration                  │
    │                                                                 │
    │  [2] SSE Transport (Web Browsers)                              │
    │      → Server-Sent Events                                      │
    │      → http://0.0.0.0:8009/sse                                 │
    │      → Perfect for web-based clients                           │
    │                                                                 │
    │  [3] HTTP Transport (API Integrations)                         │
    │      → Streamable HTTP                                         │
    │      → http://0.0.0.0:8008/mcp                                 │
    │      → REST API compatible                                     │
    │                                                                 │
    │  [0] Exit                                                       │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
    """
    print(menu)


def run_server(choice: str) -> None:
    """Run the selected server"""
    scripts = {
        "1": ("STDIO", "run_server.py"),
        "2": ("SSE", "run_server_sse.py"),
        "3": ("HTTP", "run_server_http.py"),
    }

    if choice not in scripts:
        print("\n❌ Invalid choice!")
        return

    transport_name, script_name = scripts[choice]
    script_path = Path(__file__).parent / script_name

    if not script_path.exists():
        print(f"\n❌ Error: {script_name} not found!")
        print(f"   Expected location: {script_path}")
        return

    print(f"\n🚀 Starting {transport_name} Transport...")
    print(f"   Script: {script_name}")

    if choice == "2":
        print(f"   URL: http://0.0.0.0:8009/sse")
        print(f"   Press Ctrl+C to stop")
    elif choice == "3":
        print(f"   URL: http://0.0.0.0:8008/mcp")
        print(f"   Press Ctrl+C to stop")

    print()
    print("─" * 70)
    print()

    try:
        # Run the server script
        subprocess.run([sys.executable, str(script_path)], check=True)
    except KeyboardInterrupt:
        print("\n\n⚠️  Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Server exited with error code {e.returncode}")
    except Exception as e:
        print(f"\n❌ Error: {e}")


def main():
    """Main entry point"""
    print_banner()

    while True:
        print_menu()

        try:
            choice = input("    Enter your choice [0-3]: ").strip()
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            sys.exit(0)
        except EOFError:
            print("\n\n👋 Goodbye!")
            sys.exit(0)

        if choice == "0":
            print("\n👋 Goodbye!")
            sys.exit(0)

        if choice in ["1", "2", "3"]:
            run_server(choice)
            print("\n" + "=" * 70)
            print("Server stopped. Returning to menu...")
            print("=" * 70 + "\n")
        else:
            print("\n❌ Invalid choice! Please select 0-3.\n")


if __name__ == "__main__":
    main()
