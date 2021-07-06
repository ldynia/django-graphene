#!/bin/sh

export CONTAINER_IP=$(hostname -i)
export CONTAINER_GATEWAY=$(hostname -i | sed 's/.$/1/')
echo "Container Gateway: $CONTAINER_GATEWAY"
echo "Container IP: $CONTAINER_IP"

echo "Install requirements.txt"
pip install -U pip -r /app/requirements.txt --no-cache-dir

echo "Run migrations"
python /app/manage.py makemigrations
python /app/manage.py migrate
python /app/manage.py collectstatic --noinput

# no args empty
if [ -z "$@" ]; then
    echo "Run Server"
    python /app/manage.py runserver 0.0.0.0:$PORT
else
    echo "Executeing \$@ command: $@"
    exec $@
fi