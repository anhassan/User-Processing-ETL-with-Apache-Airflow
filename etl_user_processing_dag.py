from airflow.models import DAG
from datetime import datetime, timedelta
from airflow.providers.sqlite.operators.sqlite import SqliteOperator
from airflow.providers.http.sensors.http import HttpSensor
from airflow.operators.http_operator import SimpleHttpOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator

import json
import pandas as pd


def _processing_user(ti):
    user_raw = ti.xcom_pull(task_ids=['user_fetching'])[0]
    if user_raw is not None and "results" in user_raw:
        user = user_raw['results'][0]
        user_json = {"email": user['email'],
                     "firstname": user['name']['first'],
                     "lastname": user['name']['last'],
                     "country": user['location']['country'],
                     "username": user['login']['username'],
                     "password": user['login']['password']}
        user_df = pd.DataFrame([user_json])
        user_df.to_csv('/tmp/users.csv', index=False, header=False)


default_args = {'start_date': datetime(2021, 2, 5)}
dag = DAG(dag_id="user_processing",
          default_args=default_args,
          catchup=False,
          schedule_interval=timedelta(1)
          )

create_table_task = SqliteOperator(
    task_id="create_table",
    sqlite_conn_id='db_sqlite',
    sql='''
    CREATE TABLE IF NOT EXISTS users(
    email TEXT NOT NULL PRIMARY KEY,
    firstname TEXT NOT NULL,
    lastname TEXT NOT NULL,
    country TEXT NOT NULL,
    username TEXT NOT NULL,
    password TEXT NOT NULL
);''',
    dag=dag
)

is_api_available_task = HttpSensor(
    task_id="sense_api_presence",
    http_conn_id="user_api",
    endpoint="api/",
    method="GET",
    dag=dag
)

user_fetching_task = SimpleHttpOperator(
    task_id="fetch_user",
    http_conn_id="user_api",
    endpoint="api/",
    method="GET",
    response_filter=lambda response: json.loads(response.text),
    log_response=True,
    dag=dag
)

user_filtering_task = PythonOperator(
    task_id="filter_user",
    python_callable=_processing_user,
    dag=dag
)

user_storing_task = BashOperator(
    task_id="persist_user",
    bash_command='echo -e ".separator ","\n.import /tmp/users.csv users" | sqlite3 /home/airflow/airflow/airflow.db',
    dag=dag
)

create_table_task >> is_api_available_task >> user_fetching_task >> user_filtering_task >> user_storing_task
