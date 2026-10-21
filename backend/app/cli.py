"""Admin commands: `python -m app.cli create-user <name>` / `set-password <name>`."""

import argparse
import sys
from getpass import getpass

from sqlmodel import Session, select

from .auth import hash_password
from .db import get_engine
from .models import User

MIN_PASSWORD_LENGTH = 8


def _prompt_password() -> str:
    password = getpass("Password: ")
    if len(password) < MIN_PASSWORD_LENGTH:
        sys.exit(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if getpass("Confirm password: ") != password:
        sys.exit("Passwords do not match.")
    return password


def create_user(username: str) -> None:
    with Session(get_engine()) as session:
        if session.exec(select(User).where(User.username == username)).first():
            sys.exit(f"User '{username}' already exists.")
        session.add(User(username=username, password_hash=hash_password(_prompt_password())))
        session.commit()
    print(f"Created user '{username}'.")


def set_password(username: str) -> None:
    with Session(get_engine()) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        if user is None:
            sys.exit(f"No user named '{username}'.")
        user.password_hash = hash_password(_prompt_password())
        session.add(user)
        session.commit()
    print(f"Updated password for '{username}'.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (("create-user", "add a login"), ("set-password", "reset a password")):
        commands.add_parser(name, help=help_text).add_argument("username")
    args = parser.parse_args(argv)

    if args.command == "create-user":
        create_user(args.username)
    else:
        set_password(args.username)


if __name__ == "__main__":
    main()
