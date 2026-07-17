# AgentHound backend container (Phase 1 / MVP).
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AGENTHOUND_DATA_DIR=/data

WORKDIR /srv

# Install dependencies from pyproject (single source of truth) so the image can
# never drift from project metadata. tomllib is stdlib on Python 3.11. The
# dependency list is passed to pip as an argv list from within Python, so the
# shell never parses the requirement strings (no word-splitting, globbing of
# extras like [standard], or misreading of >= version specifiers). The package
# itself is not built/installed; the app runs from source (COPY app), which
# keeps the YAML catalogs available as files at their expected paths.
COPY pyproject.toml ./
RUN python -c "import subprocess, tomllib; f = open('pyproject.toml', 'rb'); deps = tomllib.load(f)['project']['dependencies']; f.close(); subprocess.check_call(['pip', 'install', '--no-cache-dir', *deps])"

COPY app ./app

RUN mkdir -p /data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
