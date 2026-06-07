#!/bin/bash
# Настройка nginx-проброса для redirect-сервиса
# Запускать с sudo: sudo bash nginx_setup.sh

set -e

echo "=== Настройка nginx для tg.hcs-tomsk.ru ==="

# 1. Создаём конфиг
cat > /etc/nginx/sites-available/tg-redirect.conf << 'NGINX'
server {
    listen 80;
    server_name tg.hcs-tomsk.ru;

    location /b/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
    }
}
NGINX

echo "Конфиг создан: /etc/nginx/sites-available/tg-redirect.conf"

# 2. Включаем (если симлинка ещё нет)
if [ ! -L /etc/nginx/sites-enabled/tg-redirect.conf ]; then
    ln -s /etc/nginx/sites-available/tg-redirect.conf /etc/nginx/sites-enabled/
    echo "Симлинк создан в sites-enabled"
else
    echo "Симлинк уже существует"
fi

# 3. Проверяем конфиг
echo ""
echo "=== Проверка конфига nginx ==="
nginx -t

# 4. Перезагружаем nginx
systemctl reload nginx
echo "nginx перезагружен"

# 5. Тест
echo ""
echo "=== Тест редиректа через nginx (порт 80) ==="
sleep 1
curl -s -o /dev/null -w "HTTP %{http_code} -> %{redirect_url}\n" http://tg.hcs-tomsk.ru/b/1
curl -s -o /dev/null -w "HTTP %{http_code} -> %{redirect_url}\n" http://tg.hcs-tomsk.ru/b/5

echo ""
echo "=== Готово ==="
echo "Ссылки работают: http://tg.hcs-tomsk.ru/b/1 .. /b/15"
