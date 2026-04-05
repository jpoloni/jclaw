# Contributing to jClaw

Thank you for your interest in contributing to jClaw!

## Development Setup

1. **Clone and install:**
   ```bash
   git clone https://github.com/yourusername/jclaw.git
   cd jclaw
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

2. **Setup services:**
   ```bash
   docker-compose up -d
   cp .env.example .env
   ```

3. **Run tests:**
   ```bash
   pytest tests/ -v
   pytest tests/ --cov=jclaw --cov-report=html
   ```

4. **Lint and format:**
   ```bash
   ruff check jclaw/ tests/
   ruff format jclaw/ tests/
   mypy jclaw/
   ```

5. **Start dev server:**
   ```bash
   jclaw serve --reload
   ```

## Code Style

- Follow PEP 8 via `ruff`
- Type hints required (mypy strict mode)
- Docstrings for all public functions
- Tests for new features (pytest)
- Commit messages: conventional commits

## Pull Request Process

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and commit
3. Push: `git push origin feature/your-feature`
4. Open PR with description of changes
5. Wait for CI and review approval
6. Squash and merge when approved

## Commit Message Format

```
type(scope): short description

Longer description explaining the changes...

Fixes #123
Co-Authored-By: Your Name <you@example.com>
```

Types: feat, fix, docs, style, refactor, test, chore

## Questions?

Open an issue or contact the maintainers.

---

**jClaw Team**
