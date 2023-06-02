# ETL Pipeline on Airflow

## Overview:

The goal of this task is to design an Airflow DAG that fetches weather forecast data from an API, transforms it, and loads it into a PostgreSQL database with daily partitioning. The DAG should be scheduled to run once per day at 8:00 am HKT.

## Design:

The DAG consists of three tasks:

1. extract_data: Fetches the weather forecast data from the HKO weather forecast API and stores it in an XCom variable.
2. transform_data: Transforms the weather forecast data by setting the correct time format and stores the transformed data in an XCom variable.
3. load_data: Loads the transformed weather forecast data into a PostgreSQL database with daily partitioning.
The DAG is scheduled to run once per day at 8:00 am HKT using the schedule parameter.

## Implementation:

The DAG is defined in a Python file, which can be stored in the dags directory of your Airflow installation. Here's an example implementation of the DAG:

```python
import logging
from datetime import datetime
import requests
import psycopg2
from airflow import DAG
from airflow.operators.python import PythonOperator

dag = DAG(
    dag_id="hko_weather_forecast",
    start_date=datetime(2023, 5, 27),
    schedule="0 0 * * *",
)


def fetch_data():
    url = 'https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=fnd&lang=tc'
    response = requests.get(url)
    response.encoding = 'utf-8'
    try:
        data = response.json()
        return data
    except ValueError as e:
        logging.error(f"Error parsing response as JSON: {e}")
        raise


extract_data = PythonOperator(
    task_id='extract_data',
    python_callable=fetch_data,
    dag=dag
)


def transform_data(**context):
    data = context['ti'].xcom_pull(task_ids='extract_data')
    forecast_list = data['weatherForecast']
    for forecast in forecast_list:
        try:
            # Extract the date string from the forecastDate key
            date_str = forecast['forecastDate']
            # Convert the date string to a datetime object with the format '%Y%m%d'
            date_obj = datetime.strptime(date_str, '%Y%m%d').date()
            # Replace the date string with the datetime object as a string with format '%Y-%m-%d' to be saved in the database'
            forecast['forecastDate'] = date_obj.strftime('%Y-%m-%d')
        except KeyError as e:
            logging.error(f"Error processing forecast {forecast}: {e}")
        except Exception as e:
            logging.error(f"Error processing forecast {forecast}: {e}")
            raise
    return forecast_list


transform_data = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    op_kwargs={
        'data': "{{ ti.xcom_pull(task_ids='extract_data') }}"},
    dag=dag
)

def load_data(**context):
    transformed_data = context['ti'].xcom_pull(task_ids='transform_data')
    try:
        conn = psycopg2.connect(
            host='postgres',
            port='5432',
            dbname='postgres',
            user='airflow',
            password='airflow',
        )

        cur2 = conn.cursor()
        cur2.execute("SELECT version();")
        db_version = cur2.fetchone()
        print("Connected to the database. PostgreSQL version:", db_version[0])

        # Create a new table in the database for daily partitioning
        partition_name = 'weather_forecast_' + datetime.today().strftime('%Y%m%d')
        cur2.execute(f"""
        CREATE TABLE IF NOT EXISTS {partition_name} (
            id SERIAL PRIMARY KEY,
            forecast_date DATE NOT NULL,
            week TEXT,
            forecast_wind TEXT,
            forecast_weather TEXT,
            forecast_maxtemp_value INTEGER,
            forecast_maxtemp_unit TEXT,
            forecast_mintemp_value INTEGER,
            forecast_mintemp_unit TEXT,
            forecast_maxrh_value INTEGER,
            forecast_maxrh_unit TEXT,
            forecast_minrh_value INTEGER,
            forecast_minrh_unit TEXT,
            forecast_icon INTEGER,
            psr TEXT
        )
        """)

        for item in transformed_data:
            partition_name = 'weather_forecast_' + \
                datetime.today().strftime('%Y%m%d')
            sql = f"""INSERT INTO {partition_name} (
                        forecast_date, week, forecast_wind, forecast_weather,
                        forecast_maxtemp_value, forecast_maxtemp_unit, forecast_mintemp_value, forecast_mintemp_unit,
                        forecast_maxrh_value, forecast_maxrh_unit, forecast_minrh_value, forecast_minrh_unit, forecast_icon, psr
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )"""
            values = (
                item['forecastDate'],
                item['week'],
                item['forecastWind'],
                item['forecastWeather'],
                item['forecastMaxtemp']['value'],
                item['forecastMaxtemp']['unit'],
                item['forecastMintemp']['value'],
                item['forecastMintemp']['unit'],
                item['forecastMaxrh']['value'],
                item['forecastMaxrh']['unit'],
                item['forecastMinrh']['value'],
                item['forecastMinrh']['unit'],
                item['ForecastIcon'],
                item['PSR']
            )
            cur2.execute(sql, values)
            conn.commit()

    except psycopg2.Error as e:
        print("Unable to connect to the database:", e)

    finally:
        if conn is not None:
            conn.close()
            print("Database connection closed.")


load_data = PythonOperator(
    task_id='load_data',
    python_callable=load_data,
    op_kwargs={
        'transformed_data': "{{ ti.xcom_pull(task_ids='transform_data') }}"},
    dag=dag
)

extract_data >> transform_data >> load_data

```

# Cloud Infrastructure and Containerization

## Overview:

The goal of this task is to design a Dockerfile and docker-compose.yml file that create a local setup for Apache Airflow, including the web server, scheduler, and a PostgreSQL database. The DAG implemented above should be packed inside the Airflow instance. The official Airflow Docker image is used.

## Design:

The Dockerfile should be used to create a custom image for Airflow with all the necessary dependencies and configurations. The docker-compose.yml file should define the services for the web server, scheduler, and PostgreSQL database, and specify their dependencies.

_The Dockerfile should include the following steps:_

1. Start from the official Airflow image for the desired version.
2. Install any additional dependencies required for the DAG and PostgreSQL. In this case, we need to install psycopg2-binary to work with PostgreSQL.
3. Create directories for the DAGs, logs, plugins, and configuration files.
4. Create a .env file to set the AIRFLOW_UID environment variable.
5. Expose a port to access the Airflow web server.

_The docker-compose.yml file should define the following services:_

1. postgres: A PostgreSQL database service with persistent storage.
2. webserver: The Airflow web server service, which depends on the postgres service.
3. scheduler: The Airflow scheduler service, which also depends on the postgres service.
The docker-compose.yml file should also configure the environment variables required for the PostgreSQL connection and the DAG schedule.

## Implementation:

### Using Docker Compose

To set up the Airflow instance using Docker Compose, follow these steps:

1. Make sure you have Docker and Docker Compose installed on your system.
2. Download the project from GitHub: git clone https://github.com/iampattyful/data-engineer-test/
3. Once downloaded, go to the project directory
4. Open a terminal window and navigate to the root directory of your project.
5. Run the following command to start the Airflow services:

```
docker-compose up
```

This command will start the PostgreSQL, web server, and scheduler services, and will output the logs to the terminal. Once the services are up and running, you can access the Airflow web interface by opening a browser and navigating to http://localhost:8080.  

To stop the Airflow services, hit `Ctrl+C` in the terminal window where the services are running.  

To completely clean up the Airflow services and the PostgreSQL volumes, follow these steps:

1. Open a terminal window and navigate to the root directory of your project.
2. Run the following command to stop and remove the Airflow containers and volumes:

```
docker-compose down --volumes --remove-orphans
```

This command will stop and remove the Airflow containers and volumes, including the PostgreSQL data.

### Setting up the DAG in the Airflow Web Interface

To set up the DAG in the Airflow web interface, follow these steps:

1. Open a browser and navigate to http://localhost:8080.  
2. Login to the Airflow web interface using the default username and password (airflow).
3. In the Airflow web interface, clickon the "Admin" dropdown menu and select "Connections" to set up a new connection to the PostgreSQL database.  
4. Click on the "Create" button and fill in the following connection details:

- Conn Id: postgres
- Conn Type: Postgres
- Host: postgres
- Schema: postgres
- Login: airflow
- Password: airflow
- Port: 5432  

5. Click on the "Save" button to create the connection.  
6. Click on the "DAGs" menu and select the "hko_weather_forecast" DAG to view its details.  
7. Click on the "Toggle DAG Runs" button to enable the DAG schedule.  
8. Click on the "Trigger DAG" button to manually run the DAG for the first time.  

You can view the progress and logs of the DAG run in the Airflow web interface.  

Here's an example implementation of the `Dockerfile`:

```Dockerfile
# Use the official Airflow Docker image as a parent image
FROM apache/airflow:2.6.1

# Install additional dependencies
RUN pip install apache-airflow psycopg2-binary

# Create directories
RUN mkdir -p ./dags ./logs ./plugins ./config

# Create .env file
RUN echo "AIRFLOW_UID=$(id -u)" > .env

# Expose ports
EXPOSE 8080

# Start the web server and scheduler
CMD airflow scheduler & airflow webserver

```

And here's an example implementation of the `docker-compose.yaml` file:

```yaml
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

# Basic Airflow cluster configuration for CeleryExecutor with Redis and PostgreSQL.
#
# WARNING: This configuration is for local development. Do not use it in a production deployment.
#
# This configuration supports basic configuration using environment variables or an .env file
# The following variables are supported:
#
# AIRFLOW_IMAGE_NAME           - Docker image name used to run Airflow.
#                                Default: apache/airflow:2.6.1
# AIRFLOW_UID                  - User ID in Airflow containers
#                                Default: 50000
# AIRFLOW_PROJ_DIR             - Base path to which all the files will be volumed.
#                                Default: .
# Those configurations are useful mostly in case of standalone testing/running Airflow in test/try-out mode
#
# _AIRFLOW_WWW_USER_USERNAME   - Username for the administrator account (if requested).
#                                Default: airflow
# _AIRFLOW_WWW_USER_PASSWORD   - Password for the administrator account (if requested).
#                                Default: airflow
# _PIP_ADDITIONAL_REQUIREMENTS - Additional PIP requirements to add when starting all containers.
#                                Use this option ONLY for quick checks. Installing requirements at container
#                                startup is done EVERY TIME the service is started.
#                                A better way is to build a custom image or extend the official image
#                                as described in https://airflow.apache.org/docs/docker-stack/build.html.
#                                Default: ''
#
# Feel free to modify this file to suit your needs.
---
version: "3.8"
x-airflow-common: &airflow-common
  # In order to add custom dependencies or upgrade provider packages you can use your extended image.
  # Comment the image line, place your Dockerfile in the directory where you placed the docker-compose.yaml
  # and uncomment the "build" line below, Then run `docker-compose build` to build the images.
  image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:2.6.1}
  # build: .
  environment: &airflow-common-env
    AIRFLOW__CORE__EXECUTOR: CeleryExecutor
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    # For backward compatibility, with Airflow <2.3
    AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__BROKER_URL: redis://:@redis:6379/0
    AIRFLOW__CORE__FERNET_KEY: ""
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: "true"
    AIRFLOW__CORE__LOAD_EXAMPLES: "true"
    AIRFLOW__API__AUTH_BACKENDS: "airflow.api.auth.backend.basic_auth,airflow.api.auth.backend.session"
    AIRFLOW_DATABASE_URL: postgresql+psycopg2://airflow:airflow@postgres/airflow
    # yamllint disable rule:line-length
    # Use simple http server on scheduler for health checks
    # See https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/logging-monitoring/check-health.html#scheduler-health-check-server
    # yamllint enable rule:line-length
    AIRFLOW__SCHEDULER__ENABLE_HEALTH_CHECK: "true"
    # WARNING: Use _PIP_ADDITIONAL_REQUIREMENTS option ONLY for a quick checks
    # for other purpose (development, test and especially production usage) build/extend Airflow image.
    _PIP_ADDITIONAL_REQUIREMENTS: ${_PIP_ADDITIONAL_REQUIREMENTS:-}
  volumes:
    - ${AIRFLOW_PROJ_DIR:-.}/dags:/opt/airflow/dags
    - ${AIRFLOW_PROJ_DIR:-.}/logs:/opt/airflow/logs
    - ${AIRFLOW_PROJ_DIR:-.}/config:/opt/airflow/config
    - ${AIRFLOW_PROJ_DIR:-.}/plugins:/opt/airflow/plugins
    - ./data:/opt/airflow/data
  user: "${AIRFLOW_UID:-50000}:0"
  networks:
    - my_network
  depends_on: &airflow-common-depends-on
    redis:
      condition: service_healthy
    postgres:
      condition: service_healthy

services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
      POSTGRES_PORT: 5432
    ports:
      - "5432:5432"
    expose:
      - 5432
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - my_network
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 10s
      retries: 5
      start_period: 5s
    restart: always

  redis:
    image: redis:latest
    expose:
      - 6379
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 30s
      retries: 50
      start_period: 30s
    restart: always
    networks:
      - my_network

  airflow-webserver:
    <<: *airflow-common
    command: webserver
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always
    networks:
      - my_network
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-scheduler:
    <<: *airflow-common
    command: scheduler
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8974/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully
    networks:
      - my_network

  airflow-worker:
    <<: *airflow-common
    command: celery worker
    healthcheck:
      test:
        - "CMD-SHELL"
        - 'celery --app airflow.executors.celery_executor.app inspect ping -d "celery@$${HOSTNAME}"'
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    environment:
      <<: *airflow-common-env
      # Required to handle warm shutdown of the celery workers properly
      # See https://airflow.apache.org/docs/docker-stack/entrypoint.html#signal-propagation
      DUMB_INIT_SETSID: "0"
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully
    networks:
      - my_network

  airflow-triggerer:
    <<: *airflow-common
    command: triggerer
    healthcheck:
      test:
        [
          "CMD-SHELL",
          'airflow jobs check --job-type TriggererJob --hostname "$${HOSTNAME}"',
        ]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully
    networks:
      - my_network

  airflow-init:
    <<: *airflow-common
    entrypoint: /bin/bash
    # yamllint disable rule:line-length
    command:
      - -c
      - |
        function ver() {
          printf "%04d%04d%04d%04d" $${1//./ }
        }
        airflow_version=$$(AIRFLOW__LOGGING__LOGGING_LEVEL=INFO && gosu airflow airflow version)
        airflow_version_comparable=$$(ver $${airflow_version})
        min_airflow_version=2.2.0
        min_airflow_version_comparable=$$(ver $${min_airflow_version})
        if (( airflow_version_comparable < min_airflow_version_comparable )); then
          echo
          echo -e "\033[1;31mERROR!!!: Too old Airflow version $${airflow_version}!\e[0m"
          echo "The minimum Airflow version supported: $${min_airflow_version}. Only use this or higher!"
          echo
          exit 1
        fi
        if [[ -z "${AIRFLOW_UID}" ]]; then
          echo
          echo -e "\033[1;33mWARNING!!!: AIRFLOW_UID not set!\e[0m"
          echo "If you are on Linux, you SHOULD follow the instructions below to set "
          echo "AIRFLOW_UID environment variable, otherwise files will be owned by root."
          echo "For other operating systems you can get rid of the warning with manually created .env file:"
          echo "    See: https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html#setting-the-right-airflow-user"
          echo
        fi
        one_meg=1048576
        mem_available=$$(($$(getconf _PHYS_PAGES) * $$(getconf PAGE_SIZE) / one_meg))
        cpus_available=$$(grep -cE 'cpu[0-9]+' /proc/stat)
        disk_available=$$(df / | tail -1 | awk '{print $$4}')
        warning_resources="false"
        if (( mem_available < 4000 )) ; then
          echo
          echo -e "\033[1;33mWARNING!!!: Not enough memory available for Docker.\e[0m"
          echo "At least 4GB of memory required. You have $$(numfmt --to iec $$((mem_available * one_meg)))"
          echo
          warning_resources="true"
        fi
        if (( cpus_available < 2 )); then
          echo
          echo -e "\033[1;33mWARNING!!!: Not enough CPUS available for Docker.\e[0m"
          echo "At least 2 CPUs recommended. You have $${cpus_available}"
          echo
          warning_resources="true"
        fi
        if (( disk_available < one_meg * 10 )); then
          echo
          echo -e "\033[1;33mWARNING!!!: Not enough Disk space available for Docker.\e[0m"
          echo "At least 10 GBs recommended. You have $$(numfmt --to iec $$((disk_available * 1024 )))"
          echo
          warning_resources="true"
        fi
        if [[ $${warning_resources} == "true" ]]; then
          echo
          echo -e "\033[1;33mWARNING!!!: You have not enough resources to run Airflow (see above)!\e[0m"
          echo "Please follow the instructions to increase amount of resources available:"
          echo "   https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html#before-you-begin"
          echo
        fi
        mkdir -p /sources/logs /sources/dags /sources/plugins
        chown -R "${AIRFLOW_UID}:0" /sources/{logs,dags,plugins}
        exec /entrypoint airflow version
    # yamllint enable rule:line-length
    environment:
      <<: *airflow-common-env
      _AIRFLOW_DB_UPGRADE: "true"
      _AIRFLOW_WWW_USER_CREATE: "true"
      _AIRFLOW_WWW_USER_USERNAME: ${_AIRFLOW_WWW_USER_USERNAME:-airflow}
      _AIRFLOW_WWW_USER_PASSWORD: ${_AIRFLOW_WWW_USER_PASSWORD:-airflow}
      _PIP_ADDITIONAL_REQUIREMENTS: ""
    user: "0:0"
    volumes:
      - ${AIRFLOW_PROJ_DIR:-.}:/sources

  airflow-cli:
    <<: *airflow-common
    profiles:
      - debug
    environment:
      <<: *airflow-common-env
      CONNECTION_CHECK_MAX_COUNT: "0"
    # Workaround for entrypoint issue. See: https://github.com/apache/airflow/issues/16252
    command:
      - bash
      - -c
      - airflow

  # You can enable flower by adding "--profile flower" option e.g. docker-compose --profile flower up
  # or by explicitly targeted on the command line e.g. docker-compose up flower.
  # See: https://docs.docker.com/compose/profiles/
  flower:
    <<: *airflow-common
    command: celery flower
    profiles:
      - flower
    ports:
      - "5555:5555"
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:5555/"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

networks:
  my_network:

volumes:
  postgres_data:
```
Congratulations! You have now set up a local Airflow instance using Docker Compose, scheduled a DAG to run daily, and learned how to clean up after using the services.
