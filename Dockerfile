FROM python:3.11-alpine as builder

WORKDIR /app
# install dependencies
RUN pip install pdm
# gcc may be needed for some dependencies
# RUN apt-get update && apt-get install -y gcc
RUN apk --no-cache add musl-dev linux-headers g++

# ADD requirements.txt /app/requirements.txt
COPY pyproject.toml pdm.lock README.md /app/
# RUN pip install .
# install pdm in .venv by default
RUN pdm install --prod --no-lock --no-editable

# run stage
# FROM python:3.11-slim as production
FROM python:3.11-alpine as production
# pip and setuptools have open vulnerabilities
RUN pip uninstall setuptools pip -y
WORKDIR /app
COPY --from=builder /app /app
COPY app /app/app
# set environment as part of CMD because pdm installs there
CMD . .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --workers 4