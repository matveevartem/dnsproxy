Simple DNS Proxy Server with Black List
================

Исходный файл: dnsproxy.py

<h4>Установка:</h4>

chmod +x dnsproxy.py

<h4>Запуск:</h4>

sudo ./dnsproxy.py [options]

sudo python3 dnsproxy.py [options]

<h4>Справка:</h4>

./dnsproxy.py -h

python3 dnsproxy.py -h

<h4>Формат файла конфигурации</h4>

[DNS Server]

ip = 8.8.8.8 # Адрес вышестоящего DNS сервера

[Black List]

test1.ru = 1.1.1.1 #если указан домен test1.ru, вернет 1.1.1.1

\*.test2.ru = 2.2.2.2 #если указан поддомен test2.ru (например www.test2.ru), вернет 2.2.2.2

test3.ru = not resolved # если указан домен test3 вернет домен не найден



<h4>Как тестировать:</h4>

команда
<strong>$ dig -p 53 @127.0.0.1 test1.ru</strong>

или прописать в resolv.conf nameserver 127.0.0.1 

<strong>$ nslookup www.test2.ru</strong>
<strong>$ resolveip test3.ru</strong>
