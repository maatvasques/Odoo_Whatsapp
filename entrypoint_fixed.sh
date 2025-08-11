#!/bin/bash
# entrypoint_fixed.sh

# Espera o PostgreSQL aceitar conexões
echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h mydb -p 5432 -U odoo; do
  sleep 1
done
echo "PostgreSQL is ready."

# Executa o comando original do Odoo
exec odoo "$@"