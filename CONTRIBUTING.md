# Contributing to youtube-shorts-pro-skill

Thanks for your interest! This guide covers dev setup, code standards, and PR process.

## Dev Environment Setup

```bash
# Clone
git clone https://github.com/ATP0925/youtube-shorts-pro-skill.git
cd youtube-shorts-pro-skill

# Python 3.12+
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

### Prerequisites

| Tool       | Version        | Purpose                       |
|------------|----------------|-------------------------------|
| Python     | 3.10+ (CI 3.12)| Runtime                       |
| FFmpeg     | 6.x+           | Audio loudness validation     |
| Chrome     | 120+           | CDP browser automation target |
| Pillow     | 10+            | Channel branding image gen    |
| Playwright | 1.40+          | CDP connection library        |

## Code Style Rules

### 1. Every `.py` file MUST have:
- `from __future__ import annotations` as the first import.
- Module-level docstring explaining what the file does.
- `__all__` listing all public symbols.
- Full type annotations on all function signatures.
- Docstrings on all public functions (Google style).

### 2. Logging — never `print()`
```python
from logger import get_logger
log = get_logger(__name__)

log.info("Uploading %s to channel %s", filename, channel_id)
log.warning("Backdrop detected — dismissing")
log.error("CDP connection failed: %s", err)
```

### 3. Constants — no magic numbers
```python
from constants import CDP_CONNECT_TIMEOUT_MS, StudioSelectors as S

await browser.connect(cdp, timeout=CDP_CONNECT_TIMEOUT_MS)
await page.locator(S.CREATE_BUTTON).click()
```

### 4. Exceptions — no bare `return False`
```python
from exceptions import CDPConnectionError, UploadError

if not reachable:
    raise CDPConnectionError(f"Cannot reach {cdp_url}")
```

### 5. Imports from sibling modules
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
```

## Verification

Before submitting, ensure all scripts compile:

```bash
python -m py_compile scripts/constants.py
python -m py_compile scripts/exceptions.py
python -m py_compile scripts/logger.py
# ... repeat for all .py files
# Or use the CI workflow:
# .github/workflows/lint.yml runs this automatically
```

## PR Process

1. Fork → create feature branch (`feat/your-feature`).
2. Follow all code style rules above.
3. Ensure `py_compile` passes for all changed files.
4. Write a clear PR description: what changed, why, how to test.
5. Keep PRs focused — one feature/fix per PR.

## Questions?

Open an issue on [GitHub](https://github.com/ATP0925/youtube-shorts-pro-skill/issues).
