\set ON_ERROR_STOP on

\if :{?database_name}
\else
  \set database_name expense_tracking_app
\endif

SELECT format('CREATE DATABASE %I', :'database_name')
WHERE NOT EXISTS (
    SELECT 1
    FROM pg_database
    WHERE datname = :'database_name'
)
\gexec
