Simple DNS Proxy Server with Black List
================

Исходный файл: dnsproxy.py

Установка
chmod +x dnsproxy.py

Запуск:
sudo ./dnsproxy.py [options]
sudo python3 dnsproxy.py [options]

Справка: 
./dnsproxy.py -h
python3 dnsproxy.py -h

Формат файла конфигурации

[DNS Server]
ip = 8.8.8.8 # Адрес вышестоящего DNS сервера

[Black List]
test1.ru = 1.1.1.1 #если указан домен test1.ru, вернет 1.1.1.1
\*.test2.ru = 2.2.2.2 #если указан поддомен test2.ru (например www.test2.ru), вернет 2.2.2.2
test3.ru = not resolved # если указан домен test3 вернет домен не найден



Как тестировать: 
команда
$ dig -p 53 @127.0.0.1 test1.ru

или прописать в resolv.conf nameserver 127.0.0.1 
$ nslookup www.test2.ru
$ resolveip test3.ru
