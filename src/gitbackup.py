import argparse
import sys
import os

def main():
    parser = argparse.ArgumentParser(description="Git-based File Backup Tool")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize a backup repository")
    init_parser.add_argument("folder", help="Folder to monitor")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start the backup watcher")

    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop the backup watcher")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show current status")

    args = parser.parse_args()

    if args.command == "init":
        print(f"Initializing backup for {args.folder}...")
        # To be implemented: GitEngine.init_repo(args.folder)
    elif args.command == "start":
        print("Starting backup watcher...")
        # To be implemented: Controller.start()
    elif args.command == "stop":
        print("Stopping backup watcher...")
        # To be implemented: Controller.stop()
    elif args.command == "status":
        print("Service is not running.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
