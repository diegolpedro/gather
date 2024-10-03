
    CREATE USER airflow_user WITH PASSWORD 'airflow_pass';
    CREATE DATABASE airflow_db WITH OWNER airflow_user;
    GRANT ALL PRIVILEGES ON DATABASE airflow_db TO airflow_user;
    GRANT ALL ON SCHEMA public TO airflow_user;