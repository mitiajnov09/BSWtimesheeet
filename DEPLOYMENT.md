# BSW ROTACIJA — запуск на своём сервере

Инструкция для одного Linux-сервера. Выберите **A: Docker с доменом** либо **B: Python + systemd**. Раздел C — локальная проверка Docker без домена. Затем используйте общие разделы настройки, копирования, восстановления и обновления.

Во всех примерах замените `rotations.example.com` своим доменом, `SERVER_IP` — адресом сервера, `USERNAME` — пользователем SSH. На рабочем сервере создайте собственный пароль администратора; локальные демонстрационные пароли в GitHub не загружены.

## Что понадобится

- Linux, например Ubuntu 24.04, постоянный локальный диск, доступ SSH и sudo.
- Для публичного доступа: домен, DNS-запись A на SERVER_IP и открытые входящие TCP 80/443. AAAA добавляйте только при настроенном IPv6. Доступ SSH сохраните.
- Один экземпляр приложения и одна общая база SQLite. MySQL/PostgreSQL устанавливать не нужно.
- Порт 8080 в публичный интернет не открывайте: в Docker он доступен прокси, при нативной установке слушает 127.0.0.1.

## A. Docker на сервере с доменом

### 1. Подключиться и установить Docker

```sh
ssh USERNAME@SERVER_IP
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
```

Добавьте официальный репозиторий Docker для своей версии Ubuntu:

```sh
sudo tee /etc/apt/sources.list.d/docker.sources > /dev/null <<EOF_DOCKER
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF_DOCKER
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo docker version
sudo docker compose version
```

Если Docker уже установлен и работает, пропустите установку. Команды сверены с [официальной инструкцией Docker для Ubuntu](https://docs.docker.com/engine/install/ubuntu/).

### 2. Скачать проект и задать домен

```sh
git clone https://github.com/mitiajnov09/BSWtimesheeet.git
cd BSWtimesheeet
cp deploy/.env.production.example .env
nano .env
```

Содержимое `.env` для этого способа:

```dotenv
APP_DOMAIN=rotations.example.com
```

Указывайте только домен, без `https://` и без пути. Настройте DNS и сетевые правила провайдера, чтобы 80/443 доходили до сервера. Caddy получит сертификат после запуска; требования описаны в [официальном HTTPS quick-start](https://caddyserver.com/docs/quick-starts/https).

### 3. Подготовить каталог копий и собрать образ

```sh
mkdir -p backups
sudo chown 10001:10001 backups
sudo chmod 700 backups
sudo docker compose build
```

Контейнер работает под UID 10001, поэтому каталогу `backups` нужен этот владелец. База будет в именованном томе `rotations_data`, внутри контейнера `/app/data/rotations.sqlite3`.

### 4. Создать базу и первого администратора

```sh
sudo docker compose run --rm app python app.py --migrate
sudo docker compose run --rm app python app.py --create-admin admin
```

Введите свой пароль дважды. Он не отображается в терминале; минимум 10 символов. Выполняйте создание первого администратора один раз. Если администратор уже существует, приложение предложит использовать интерфейс.

SQLite установлен вместе с Python. Миграции создают таблицы автоматически. Отдельные логин/пароль для SQLite не нужны.

### 5. Запустить и проверить

```sh
sudo docker compose up -d
sudo docker compose ps
sudo docker compose logs --tail=100 app
sudo docker compose logs --tail=100 proxy
```

Откройте `https://rotations.example.com`, войдите как `admin` со своим паролем. Контейнер app имеет проверку состояния; ожидаемое состояние — healthy. При первом получении сертификата запуск HTTPS может занять некоторое время.

Образы настроены перезапускаться после перезагрузки сервера. `docker compose down` сохраняет данные; **`docker compose down -v` удаляет том с базой, не используйте его для остановки или обновления.**

## B. Сервер без Docker: Python + systemd + HTTPS

Команды ниже рассчитаны на Ubuntu 24.04 с Python 3.12.

### 1. Установить Python и скачать исходники

```sh
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git
python3 --version
sudo useradd --system --home /opt/bsw-rotacija --shell /usr/sbin/nologin bsw
sudo git clone https://github.com/mitiajnov09/BSWtimesheeet.git /opt/bsw-rotacija
sudo chown -R bsw:bsw /opt/bsw-rotacija
sudo -u bsw python3 -m venv /opt/bsw-rotacija/.venv
sudo -u bsw /opt/bsw-rotacija/.venv/bin/pip install -r /opt/bsw-rotacija/requirements.txt
sudo -u bsw mkdir -p /opt/bsw-rotacija/data /opt/bsw-rotacija/backups
```

Если пользователь `bsw` уже создан, команду `useradd` пропустите. На другой ОС установите Python 3.12 средствами вашей системы, затем используйте те же команды приложения.

### 2. Настроить окружение и базу

```sh
sudo -u bsw cp /opt/bsw-rotacija/.env.example /opt/bsw-rotacija/.env
sudo nano /opt/bsw-rotacija/.env
```

Задайте:

```dotenv
APP_HOST=127.0.0.1
APP_PORT=8080
APP_DB=/opt/bsw-rotacija/data/rotations.sqlite3
APP_ORIGIN=https://rotations.example.com
APP_SECURE_COOKIE=1
```

Затем:

```sh
sudo chmod 600 /opt/bsw-rotacija/.env
sudo chown bsw:bsw /opt/bsw-rotacija/.env
sudo -u bsw /opt/bsw-rotacija/.venv/bin/python /opt/bsw-rotacija/app.py --migrate
sudo -u bsw /opt/bsw-rotacija/.venv/bin/python /opt/bsw-rotacija/app.py --create-admin admin
```

Пароль задайте собственный. `.env` не публикуется в GitHub.

### 3. Настроить автозапуск

```sh
sudo cp /opt/bsw-rotacija/deploy/bsw-rotacija.service /etc/systemd/system/bsw-rotacija.service
sudo systemctl daemon-reload
sudo systemctl enable --now bsw-rotacija
sudo systemctl status bsw-rotacija --no-pager
```

Проверьте ответ приложения и журнал:

```sh
curl -fsS http://127.0.0.1:8080/ > /dev/null
sudo journalctl -u bsw-rotacija -n 100 --no-pager
```

### 4. Установить Caddy и включить HTTPS

Для официального репозитория Caddy:

```sh
sudo apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl gnupg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg /etc/apt/sources.list.d/caddy-stable.list
sudo apt-get update
sudo apt-get install -y caddy
```

Команды установки доступны в [официальной инструкции Caddy](https://caddyserver.com/docs/install#debian-ubuntu-raspbian). Если Caddy уже установлен, этот шаг пропустите.

Скопируйте конфигурацию и замените домен:

```sh
sudo cp /opt/bsw-rotacija/deploy/Caddyfile.native.example /etc/caddy/Caddyfile
sudo nano /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Пример Caddyfile:

```caddyfile
rotations.example.com {
    encode gzip
    request_body {
        max_size 6MB
    }
    header Strict-Transport-Security "max-age=31536000"
    reverse_proxy 127.0.0.1:8080
}
```

Откройте `https://rotations.example.com`. Домен в Caddyfile и `APP_ORIGIN` должны совпадать. DNS и порты 80/443 должны быть настроены. Лимит 6 MB позволяет передать изображение до 4 MB в JSON/base64; [описание request_body](https://caddyserver.com/docs/caddyfile/directives/request_body).

## C. Локальный Docker без домена

Нужен установленный Docker Engine с Compose либо Docker Desktop. Используйте отдельный `compose.local.yaml`:

```sh
git clone https://github.com/mitiajnov09/BSWtimesheeet.git
cd BSWtimesheeet
mkdir -p backups
sudo chown 10001:10001 backups
sudo chmod 700 backups
sudo docker compose -f compose.local.yaml build
sudo docker compose -f compose.local.yaml run --rm app python app.py --create-admin admin
sudo docker compose -f compose.local.yaml up -d
```

На Docker Desktop для macOS/Windows используется механизм доступа Docker к каталогам хоста; при отказе записи проверьте доступ к папке проекта. Команды `chown`/`chmod` выше рассчитаны на Linux.

Откройте **http://127.0.0.1:8080**, не `localhost`: разрешённый источник задан именно как 127.0.0.1. Если 8080 занят локальным Python-приложением, сначала остановите его. Этот режим не предназначен для публичного доступа без HTTPS.

Локальная база хранится в отдельном томе `rotations_local_data`; она не совпадает с базой режима A. Для всех дальнейших Docker-команд этого режима добавляйте `-f compose.local.yaml` либо используйте `scripts/backup-docker.sh local`.

## После первого входа

1. Создайте объект: название, страну, город и часовой пояс IANA, например `Europe/Vilnius`.
2. Создайте проект с объектом и датами. Откройте его график.
3. Добавьте работников из списка либо создайте карточки. Работники не получают учётных записей. Фото можно загрузить в карточке администратора.
4. Создайте команды и назначьте состав. TL/WM выбираются в карточке работника.
5. Создайте руководителей и секретарей в разделе учётных записей. В карточке проекта отметьте пользователей, которым нужен доступ.
6. Постройте циклы, добавьте исключения и поездки. Проверьте сохранение после обновления страницы.
7. Проверьте PDF с фото и без, отзыв со скриншотом и просмотр отзыва администратором.
8. Войдите как руководитель/секретарь и проверьте назначенный проект и ограничения роли.

## Резервное копирование

### Одна команда

На Python-установке:

```sh
sudo -u bsw /opt/bsw-rotacija/.venv/bin/python /opt/bsw-rotacija/backup.py
```

Создаётся датированный файл в `/opt/bsw-rotacija/backups/`. Скрипт сам загружает APP_DB из `.env`, использует SQLite Backup, проверяет целостность и связи, задаёт права 600. Он **не требует остановки приложения**. Фотографии и скриншоты включены в копию.

На Docker-установке, из папки репозитория:

```sh
sudo ./scripts/backup-docker.sh
```

Копия появится в каталоге `backups` хоста. Для локального Docker: `sudo ./scripts/backup-docker.sh local`.

Можно задать своё имя:

```sh
sudo docker compose exec -T app python backup.py /backups/manual-copy.sqlite3
```

Существующий файл не перезаписывается. Используйте новое имя для каждой копии. Скрипты `backup.py` и `restore.py` работают на стандартной библиотеке Python.

### Ежедневный запуск

Docker: выполните `sudo crontab -e` и добавьте строку, заменив путь на фактический путь репозитория:

```cron
0 3 * * * /absolute/path/BSWtimesheeet/scripts/backup-docker.sh >> /var/log/bsw-rotacija-backup.log 2>&1
```

Нативный Python: в `sudo crontab -e`:

```cron
0 3 * * * /usr/sbin/runuser -u bsw -- /opt/bsw-rotacija/.venv/bin/python /opt/bsw-rotacija/backup.py >> /var/log/bsw-rotacija-backup.log 2>&1
```

Проверьте время/часовой пояс сервера. Автоматическая очистка копий не включена: проверяйте свободное место и храните выбранные копии отдельно от сервера. Копии содержат данные сотрудников, фото, отзывы и хеши паролей.

## Восстановление копии

Сначала остановите приложение, сохраните текущую базу отдельной копией и выберите файл для восстановления. При восстановлении возвращаются данные, пользователи и пароли из выбранной копии.

### Docker

Из папки проекта, заменив имя файла:

```sh
sudo docker compose stop app
sudo docker compose run --rm app python backup.py /backups/before-restore.sqlite3
sudo docker compose run --rm app python restore.py /backups/bsw-rotacija-ДАТА.sqlite3 --replace
sudo docker compose run --rm app python app.py --migrate
sudo docker compose up -d app
```

Если `before-restore.sqlite3` уже есть, задайте другое имя. `restore.py` проверяет копию и заменяет данные через SQLite Backup, а не простым копированием файлов с устаревшим WAL. Не запускайте восстановление одновременно с работающим app.

### Нативный Python

```sh
sudo systemctl stop bsw-rotacija
sudo -u bsw /opt/bsw-rotacija/.venv/bin/python /opt/bsw-rotacija/backup.py
sudo -u bsw /opt/bsw-rotacija/.venv/bin/python /opt/bsw-rotacija/restore.py /opt/bsw-rotacija/backups/bsw-rotacija-ДАТА.sqlite3 --replace
sudo -u bsw /opt/bsw-rotacija/.venv/bin/python /opt/bsw-rotacija/app.py --migrate
sudo systemctl start bsw-rotacija
```

Без `--replace` восстановление не заменит существующую базу. Если текущая база повреждена и Backup не выполняется, сначала сохраните её файл вместе с `-wal`/`-shm` отдельно, затем восстанавливайте проверенную копию.

## Обновление версии

### Docker

```sh
sudo ./scripts/backup-docker.sh
git pull --ff-only
sudo docker compose build
sudo docker compose stop app
sudo docker compose run --rm app python app.py --migrate
sudo docker compose up -d
sudo docker compose ps
```

Не удаляйте постоянный том. Если изменился Dockerfile, обязательно пересоберите образ. `.env` и каталог `backups` Git не изменяет.

### Нативный Python

```sh
sudo -u bsw /opt/bsw-rotacija/.venv/bin/python /opt/bsw-rotacija/backup.py
sudo systemctl stop bsw-rotacija
sudo -u bsw git -C /opt/bsw-rotacija pull --ff-only
sudo -u bsw /opt/bsw-rotacija/.venv/bin/pip install -r /opt/bsw-rotacija/requirements.txt
sudo -u bsw /opt/bsw-rotacija/.venv/bin/python /opt/bsw-rotacija/app.py --migrate
sudo systemctl start bsw-rotacija
```

Для отката сохраните исходники нужной версии и соответствующую ей копию базы. Затем остановите app, верните код, восстановите копию и запустите. Не запускайте старую версию с неизвестной ей новой схемой базы.

## Если что-то не запускается

| Симптом | Что проверить |
| --- | --- |
| HTTPS не открывается | DNS A/AAAA, доступность TCP 80/443, логи proxy/Caddy, отсутствие другого сервиса на тех же портах |
| Ошибка источника запроса | Полный APP_ORIGIN и адрес в браузере: схема, домен и порт должны совпадать |
| Вход не сохраняется при HTTP | APP_SECURE_COOKIE=1 рассчитан на HTTPS; для локальной проверки используйте режим C или `.env.example` |
| Нет администратора | Создайте первого через `app.py --create-admin admin`, не ищите готовый пароль в репозитории |
| Фото не загружается | PNG/JPEG/WebP до 4 МБ, актуальный Caddyfile с max_size 6MB; сторонний прокси должен пропускать такой запрос |
| Backup: Permission denied | Владелец backups в Docker UID 10001; при нативной установке пользователь bsw |
| SQLite: readonly / database locked | Права на data и сам файл, локальный диск, один экземпляр приложения; не используйте сетевую папку |
| В Docker пропали данные | Правильный Compose-проект/том; локальный и серверный тома разные. Проверьте, не был ли выполнен down -v |

## Что проверено в этой версии

Серверные функции, ограничения ролей, миграции, PDF, JavaScript-логика и отдельное резервное копирование/восстановление проверяются локально. Docker отсутствует в среде разработки, поэтому сборка образа, Caddy/HTTPS, systemd и реальный сервер здесь не запускались. Эти инструкции и конфигурации необходимо проверить на выбранном сервере; такая проверка не заменена заявлением о готовом размещении.
