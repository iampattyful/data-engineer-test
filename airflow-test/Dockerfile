# Use the official Airflow Docker image as a parent image
FROM apache/airflow:2.6.1

# Install additional dependencies
RUN pip install apache-airflow psycopg2-binary

# Create directories
RUN mkdir -p ./dags ./logs ./plugins ./config

# Create .env file
RUN echo -e "AIRFLOW_UID=$(id -u)" > .env

# Expose ports
EXPOSE 8080

# Start the web server and scheduler
CMD airflow scheduler & airflow webserver
