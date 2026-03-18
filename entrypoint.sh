#!/bin/bash
echo "Starting the application"

until python3 ./manage.py check 2> /dev/null; do
    echo "Waiting for errors to be gone..."
    sleep 1
done

python3 ./manage.py migrate --noinput
python3 ./manage.py setup_cinema

exec "$@"