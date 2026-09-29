from pathlib import Path
import re
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent


def test_gitignore_excludes_env_files():
    """
    Verifies that .gitignore contains exclusions for .env and .env.* while permitting .env.example.
    """
    gitignore_path = REPO_ROOT / ".gitignore"
    assert gitignore_path.exists(), ".gitignore file must exist at repository root"
    content = gitignore_path.read_text(encoding="utf-8")

    assert ".env" in content
    assert ".env.*" in content
    assert "!.env.example" in content


def test_env_example_files_exist():
    """
    Verifies that .env.example files exist in both frontend and backend directories.
    """
    frontend_env = REPO_ROOT / "frontend" / ".env.example"
    backend_env = REPO_ROOT / "backend" / ".env.example"

    assert frontend_env.exists(), "frontend/.env.example must exist"
    assert backend_env.exists(), "backend/.env.example must exist"

    # Check contents do not contain actual live secrets
    frontend_content = frontend_env.read_text(encoding="utf-8")
    backend_content = backend_env.read_text(encoding="utf-8")

    assert "your-project" in frontend_content or "your-" in frontend_content
    assert "your-project" in backend_content or "your-" in backend_content


def test_no_actual_env_in_git():
    """
    Ensures that no live .env file is present or committed.
    """
    assert not (REPO_ROOT / ".env").exists()
    assert not (REPO_ROOT / "backend" / ".env").exists()
    assert not (REPO_ROOT / "frontend" / ".env").exists()


def test_no_hardcoded_secrets_in_code():
    """
    Scans backend python and migration files for hardcoded secrets or JWT tokens.
    """
    secret_patterns = [
        re.compile(r"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.[A-Za-z0-9-_]+"), # JWT regex
        re.compile(r"sbp_[a-zA-Z0-9]{30,}"), # Supabase access token
        re.compile(r"postgresql://[^:]+:[^@]+@db\.[^:]+\.supabase\.co"), # Live supabase conn string
    ]

    scanned_files = list((REPO_ROOT / "backend").rglob("*.py")) + list((REPO_ROOT / "backend").rglob("*.sql"))
    for file_path in scanned_files:
        content = file_path.read_text(encoding="utf-8")
        for pattern in secret_patterns:
            matches = pattern.findall(content)
            assert len(matches) == 0, f"Found potential secret match in {file_path}: {matches}"
