import asyncio
import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m app.cli <command>")
        print("Commands: create-superuser")
        sys.exit(1)

    command = sys.argv[1]

    if command == "create-superuser":
        email = None
        password = None
        args = sys.argv[2:]
        i = 0
        while i < len(args):
            if args[i] == "--email" and i + 1 < len(args):
                email = args[i + 1]
                i += 2
            elif args[i] == "--password" and i + 1 < len(args):
                password = args[i + 1]
                i += 2
            else:
                i += 1

        if not email or not password:
            print(
                "Usage: python -m app.cli create-superuser --email <email> --password <password>"
            )
            sys.exit(1)

        from seed import create_superuser

        asyncio.run(create_superuser(email, password))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
