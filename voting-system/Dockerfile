# Use the official Python image as a parent image
FROM python:3.10-slim-buster

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org sanic psycopg2-binary

# Install the PostgreSQL client
RUN apt-get update && apt-get install -y postgresql-client

# Set environment variables for the database connection
# ENV POSTGRES_DB=voting_system
# ENV POSTGRES_USER=postgres
# ENV POSTGRES_PASSWORD=postgres

# Expose port 8000 for the Sanic application
EXPOSE 8000

# Run start.sh when the container launches
# COPY start.sh /app/start.sh
# CMD ["/bin/bash", "/app/start.sh"]