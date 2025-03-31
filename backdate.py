import subprocess
import argparse
import os
import random
import time
from datetime import date, timedelta
from pathlib import Path


START_DATE = date(2024, 6, 1)
END_DATE = date(2025, 3, 31)
DEFAULT_SEED = 20240601
MIN_GAP = 2
MAX_GAP = 8
REPOSITORY = Path(__file__).resolve().parent

COMMIT_MESSAGES = (
    "chore: initialize TaskPilot workspace",
    "chore: add Bun workspace configuration",
    "feat: establish shared TypeScript configuration",
    "chore: configure Turborepo task pipeline",
    "feat: scaffold Elysia API application",
    "feat: scaffold Next.js web application",
    "feat: add Drizzle database package",
    "feat: define core project schema",
    "feat: add issue lifecycle model",
    "feat: add project membership permissions",
    "feat: configure Better Auth server",
    "feat: connect API sessions to Better Auth",
    "feat: add API error handling conventions",
    "feat: add project management routes",
    "feat: add issue management routes",
    "feat: validate issue creation payloads",
    "feat: assign issue sequence numbers",
    "feat: add issue status transitions",
    "feat: add issue views and filters",
    "feat: add project member invitations",
    "feat: enforce project access guards",
    "fix: prevent cross-project issue access",
    "test: cover project route permissions",
    "test: cover issue lifecycle endpoints",
    "feat: add attachment object storage",
    "fix: harden public attachment responses",
    "feat: add webhook ingestion endpoints",
    "feat: add webhook delivery records",
    "feat: retry failed webhook deliveries",
    "feat: scaffold background worker",
    "feat: add notification delivery worker",
    "feat: add Telegram bot service",
    "feat: connect bot commands to the API",
    "feat: add agent runtime package",
    "feat: add agent tool definitions",
    "feat: add agent task scheduling",
    "feat: add agent runner integration",
    "fix: validate agent task ownership",
    "test: cover webhook retry behavior",
    "test: cover agent tool authorization",
    "feat: add web authentication screens",
    "feat: add project navigation layout",
    "feat: add issue list and detail views",
    "feat: add issue editor interactions",
    "feat: add web live refresh scopes",
    "feat: add internationalized web messages",
    "feat: add Arabic and Chinese translations",
    "fix: correct right-to-left layout utilities",
    "feat: add user preference settings",
    "feat: add API documentation routes",
    "chore: add local Postgres and MinIO compose stack",
    "chore: add production compose configuration",
    "chore: add Coolify deployment configuration",
    "chore: add throwaway database test stack",
    "docs: document local development setup",
    "docs: document self-hosting deployment",
    "docs: document runner installation",
    "docs: document security reporting",
    "fix: normalize API validation errors",
    "fix: preserve last project owner protection",
    "fix: handle attachment cleanup failures",
    "test: expand membership access coverage",
    "test: expand attachment endpoint coverage",
    "test: verify complete project issue workflow",
    "chore: align Docker workspace manifests",
    "chore: configure release automation",
    "chore: add CI quality gates",
    "chore: prepare TaskPilot public release",
)


def git(*args, env=None):
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=REPOSITORY,
            env=env,
            check=True,
            text=True,
            encoding="utf-8",
            errors="surrogateescape",
            capture_output=True,
        )
    except subprocess.CalledProcessError as error:
        details = (error.stderr or error.stdout or "").strip()
        command = " ".join(["git", *args])
        raise RuntimeError(f"{command} failed: {details}") from error
    return result.stdout.strip()


def repository_files():
    paths = git("ls-files", "-co", "--exclude-standard", "-z").encode("utf-8")
    return [
        REPOSITORY / Path(raw.decode("utf-8"))
        for raw in paths.split(b"\x00")
        if raw and (REPOSITORY / Path(raw.decode("utf-8"))).is_file()
    ]


def commit_dates(seed=DEFAULT_SEED):
    generator = random.Random(seed)
    current_date = START_DATE
    while current_date <= END_DATE:
        yield current_date
        if current_date == END_DATE:
            break
        next_date = current_date + timedelta(days=generator.randint(MIN_GAP, MAX_GAP))
        current_date = min(next_date, END_DATE)


def validate_git_identity():
    missing = []
    if not git("config", "--get", "user.name"):
        missing.append("user.name")
    if not git("config", "--get", "user.email"):
        missing.append("user.email")
    if missing:
        settings = ", ".join(missing)
        raise RuntimeError(
            f"Git identity is not configured ({settings}). Set it with, for example:\n"
            "  git config user.name \"Your Name\"\n"
            "  git config user.email \"you@example.com\""
        )


def main(push=False, delay=0, dry_run=False, seed=DEFAULT_SEED):
    files = repository_files()
    if not files:
        raise RuntimeError("No tracked or untracked project files were found.")
    if not dry_run:
        validate_git_identity()

    dates = list(commit_dates(seed))
    if len(dates) > len(COMMIT_MESSAGES):
        raise RuntimeError(
            f"Add more unique commit messages: {len(dates)} commits are scheduled, "
            f"but only {len(COMMIT_MESSAGES)} messages exist."
        )

    for index, current_date in enumerate(dates):
        first = index * len(files) // len(dates)
        last = (index + 1) * len(files) // len(dates)
        changed = files[first:last]
        message = f"{COMMIT_MESSAGES[index]} ({current_date.isoformat()})"

        date_value = f"{current_date.isoformat()}T12:00:00"
        if dry_run:
            print(f"Would commit {date_value}: {message}")
        else:
            environment = os.environ.copy()
            environment["GIT_COMMITTER_DATE"] = date_value
            if changed:
                git("add", "--", *[str(path.relative_to(REPOSITORY)) for path in changed])
            git(
                "commit",
                "--allow-empty",
                "--date",
                date_value,
                "-m",
                message,
                env=environment,
            )
            print(f"Committed {current_date.isoformat()} ({len(changed)} files): {message}")
            if push:
                git("push")
        if delay:
            time.sleep(delay)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Create TaskPilot commits with deterministic random odd and even day gaps "
            "from June 2024 to March 2025."
        )
    )
    parser.add_argument("--push", action="store_true", help="Push each commit after creating it.")
    parser.add_argument("--delay", type=float, default=0, help="Seconds to wait between commits.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned dates and messages without changing files or commits.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Seed for repeatable random gaps (default: {DEFAULT_SEED}).",
    )
    arguments = parser.parse_args()
    main(
        push=arguments.push,
        delay=arguments.delay,
        dry_run=arguments.dry_run,
        seed=arguments.seed,
    )
