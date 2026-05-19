#!/bin/bash

# Прерываем выполнение скрипта, если какая-то из команд завершится ошибкой
set -e

echo "=== Ожидание готовности базы данных ==="

python << 'EOF'
import os
import sys
import asyncio
import asyncpg

async def wait_for_db():
    while True:
        try:
            conn = await asyncpg.connect(
                database=os.environ.get('DB_NAME'),
                user=os.environ.get('DB_USER'),
                password=os.environ.get('DB_PASSWORD'),
                host=os.environ.get('DB_HOST'),
                port=os.environ.get('DB_PORT', '5432')
            )
            await conn.close()
            break
        except Exception:
            sys.stdout.write("БД пока недоступна, ждем 1 секунду...\n")
            await asyncio.sleep(1)

asyncio.run(wait_for_db())
EOF
echo "=== База данных готова к подключениям! ==="


echo "=== Запуск бэкенда ==="
exec "$@"