# Introduction
This application structures and triggers an ***ETL*** pipeline using ***Apache Airflow*** to fetch users from an Api(*Extract*), filter their properties(*Transform*) and finally persist the processed users in a database(*Load*). The pipeline uses both sensor and action based operators along with cross communication between them using (**Xcom**) inside a ***DAG***(*Directed Acyclic Graph*) to trigger the workflow on a daily basis.

# Setup
To begin, apache airflow needs to be installed in the system to create a workflow. The installation of airflow is not trivial. The following steps should be taken to install airflow in order to avoid hassle.

 1. Create a python virtual environment (*venv*)
 ```python
 python3 -m venv <virtual_environment_name>
 ```
 2. Activate the virtual environment created
 ```python
 source <virtual_environment_name>/bin/activate
 ```
 3. Install wheel dependency 
 ```python 
 pip3 install wheel
 ```
 4. Install the airflow module along with the constraints option
 ```python 
 pip3 install apache-airflow=<version> --constraint <constraints>
 ```
 5. Initialize the metastore of airflow
 ```python 
 airflow db init
 ```
 6. Finally, create an airflow user to login into the airflow GUI
 ```python
 airflow users create -u <username> -p <password>
  -f <first_name> -l <last_name> -r Admin -e <email>
 ```
 7. Start the airflow webserver in a new terminal
 ```bash
 cd airflow
 ```
 ```python
 airflow webserver
 ```
 8. Start the airflow scheduler in a new terminal 
```bash
cd airflow
```
```python
airflow scheduler
```
At last airflow can be used to create our long awaited data pipeline

# Design & Implementation
The application fetches a random user from `https://randomuser.me` using the end point `/api`, then transforms the response and stores the transformed output into a table in a database. All this requires a series of tasks(known as operators in airflow) to be carried out. 

The first step requires creation of a table in the default sqlite database of airflow using the ***SqliteOperator***. This requires installing the sqlite operator using
```python
pip install 'apache-airflow-providers-sqlite'
```
In addition, a connection is also required to be added in airflow for `sqlite_conn_id`. This basically tells airflow where to find the database we are referring to.

The second step requires a sensor operator to sense whether the api is present or not. This requires installing the ***HttpSensor*** using the following command
```python
pip install 'apache-airflow-providers-http'
```  
Similar to the previous task, again a connection is required to be added in airflow but this time for `http_conn_id` which specifies the api url we need to sense. In addition the `endpoint` is also defined in the operator.

The third step requires fetching the random user from the api using `SimpleHttpOperator`. In this operator the text part of the response- received via the *GET* method is extracted.

The fourth step uses the `PythonOperator` to transform the user by filtering the required parameters from the *JSON* response and push the processed user to a csv file. But there is a need for the *JSON* response from the previous step to reach the python operator. For this purpose we use cross communication(***Xcom***) feature of airflow using `task_instance.xcom_pull(task_ids=[<task_name>])` to get the extracted response from the previous task.

The fifth and last step uses a `BashOperator` to read the data from the csv file(created in the last step) and stores it in the table created in the first step.
The dependencies among tasks are added using `>>` the bitshift operator such that if `task1>>task2` then task1 occurs before task2.

The diagram below further clarifies sequence of events in the triggered pipeline
<p align="center">
  <img src="assets/Etl_user_processing.png" />
</p>
