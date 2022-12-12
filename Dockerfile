# Base image: https://hub.docker.com/_/python
FROM python:3.11.1-slim

# Prevents Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
RUN adduser -u 5678 --disabled-password --gecos "" plexist && chown -R plexist /app
USER plexist

# During debugging, this entry point will be overridden.
CMD ["python", "plexist/plexist.py"]

# docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 -t gyarbij/plexist:<tag> --push .