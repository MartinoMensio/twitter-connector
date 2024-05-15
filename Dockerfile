FROM python:3.13.0b1-alpine as base
# move to edge, removes a lot of vulnerabilities
RUN sed -i -e 's/v[^/]*/edge/g' /etc/apk/repositories && \
    apk update && \
    apk upgrade
WORKDIR /app



# builder stage
FROM base as builder

# install dependencies
RUN pip install pdm

# add files for installation of dependencies
COPY pyproject.toml pdm.lock README.md /app/

# install pdm in .venv by default
RUN pdm install --prod --no-lock --no-editable



# production stage
FROM base as production
# pip and setuptools have open vulnerabilities, remove them
RUN pip uninstall setuptools pip -y

# files from builder
COPY --from=builder /app /app
# files from application
COPY app /app/app
# set environment and launch uvicorn
CMD . .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --workers 4