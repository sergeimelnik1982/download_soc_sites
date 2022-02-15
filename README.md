# download_soc_sites
Скрипт для скачивания списка социальных сайтов с аутентификацией по связке логин/пароль и загрузки их в БД.

Для установки:
python3 -m pip install -r requirements.txt

Создаём БД и импортируем её из soc_sites.sql

В settings.ini:

```
[rkn]
login = логин (ИНН)
password = пароль
```

```
[system]
path=/tmp/rkn.zip - куда скачиваем zip-файл
unzip_path = /tmp/ - куда разархивируем zip
```

```
[mysql]
DB = soc_inet - имя БД
username = soc_inet - пользователь БД
password = 12345 - пароль
host = localhost - хост, на котором находится БД<
port = 3306 - порт
```

Запускать:
python3 soc.py
