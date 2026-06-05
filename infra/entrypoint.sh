#!/bin/bash

# Прерываем выполнение скрипта, если какая-то из команд завершится ошибкой
set -e

echo "=== Ожидание готовности базы данных ==="

python << 'EOF'
import os
import sys
import asyncio
import asyncpg
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(10), wait=wait_fixed(2))
async def wait_for_db():
    sys.stdout.write("Попытка подключения к БД...\n")
    conn = await asyncpg.connect(
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        host=os.environ.get('DB_HOST'),
        port=os.environ.get('DB_PORT', '5432')
    )
    await conn.close()
    sys.stdout.write("БД успешно подключена!\n")

asyncio.run(wait_for_db())
EOF
echo "=== База данных готова к подключениям! ==="


echo "=== Запуск бэкенда ==="
exec "$@"