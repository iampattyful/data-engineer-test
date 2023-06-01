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
