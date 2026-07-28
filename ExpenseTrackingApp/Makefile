PSQL ?= psql
DATABASE_NAME ?= expense_tracking_app
MAINTENANCE_DB ?= postgres

.PHONY: db-create db-migrate db-setup

db-create:
	$(PSQL) -X -v ON_ERROR_STOP=1 \
		-v database_name="$(DATABASE_NAME)" \
		--dbname="$(MAINTENANCE_DB)" \
		--file=migrations/000_create_database.sql

db-migrate:
	$(PSQL) -X -v ON_ERROR_STOP=1 \
		--dbname="$(DATABASE_NAME)" \
		--file=migrations/001_create_transactions.sql
	$(PSQL) -X -v ON_ERROR_STOP=1 \
		--dbname="$(DATABASE_NAME)" \
		--file=migrations/002_reject_nan_amounts.sql

db-setup: db-create db-migrate
