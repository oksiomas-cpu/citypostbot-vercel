#!/bin/bash
# Деплой redirect-сервиса для La Ciudad de los Sentidos
# Запускать: bash redirect_deploy.sh

set -e

echo "=== Деплой redirect-сервера ==="

# 1. Копируем systemd-юнит
sudo cp /home/hcs/citypostbot/redirect.service /etc/systemd/system/redirect.service

# 2. Перезагружаем systemd
sudo systemctl daemon-reload

# 3. Включаем автозапуск
sudo systemctl enable redirect.service

# 4. Запускаем (или рестартуем если уже есть)
sudo systemctl restart redirect.service

# 5. Ждём секунду и смотрим статус
sleep 1
sudo systemctl status redirect.service --no-pager

echo ""
echo "=== Проверка редиректов ==="
echo "Тест /b/1:"
curl -s -o /dev/null -w "HTTP %{http_code} -> %{redirect_url}\n" http://localhost:8080/b/1
echo "Тест /b/5:"
curl -s -o /dev/null -w "HTTP %{http_code} -> %{redirect_url}\n" http://localhost:8080/b/5

echo ""
echo "=== Готово ==="
echo "Ссылки готовы: https://tg.hcs-tomsk.ru/b/1 .. /b/15"
