import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

# Конфигурационные данные
GIST_ID = "5d53a0965ad16d964c5fb366e11532ff"
GIST_TOKEN = os.getenv("GIST_TOKEN")
DOWNLOAD_TOKEN = "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"
SOURCE_URL = "https://raw.githubusercontent.com/Roadlux/assets-1.5.3.1/main/data"

def update():
    # Шаг 1: Скачиваем конфиг
    req = urllib.request.Request(SOURCE_URL, headers={"Authorization": f"token {DOWNLOAD_TOKEN}"})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
    
    # Шаг 2: Извлекаем fragmentServer и формируем VLESS-ссылки
    configs = []
    
    # Добавляем заголовок с временем
    ural_offset = timezone(timedelta(hours=5))
    ural_time = datetime.now(ural_offset).strftime('%d.%m.%Y %H:%M:%S')
    header_line = f"vless://00000000-0000-0000-0000-000000000000@127.0.0.1:0?type=none#🕒_Update_Ural:_{ural_time}"
    configs.append(header_line)
    
    for c in data.get('configs', []):
        fs = c.get('config', {}).get('fragmentServer')
        if fs:
            # Извлекаем параметры (ключи адаптированы под типичные структуры)
            uuid = fs.get('id', '00000000-0000-0000-0000-000000000000')
            addr = fs.get('address', '127.0.0.1')
            port = fs.get('port', 443)
            
            # Формируем имя для ссылки
            name = f"Proxy_{addr}"
            
            # Собираем ссылку. Параметры можно расширить, если нужно (security, sni, etc.)
            link = f"vless://{uuid}@{addr}:{port}?type=tcp&security=none#{urllib.parse.quote(name)}"
            configs.append(link)
    
    content = "\n".join(configs)
    
    # Шаг 3: Отправляем в Gist
    payload = json.dumps({"files": {"sub.txt": {"content": content}}}).encode('utf-8')
    gist_req = urllib.request.Request(
        f"https://api.github.com/gists/{GIST_ID}",
        data=payload,
        method="PATCH",
        headers={
            "Authorization": f"token {GIST_TOKEN}",
            "Content-Type": "application/json"
        }
    )
    
    with urllib.request.urlopen(gist_req) as response:
        if response.status == 200:
            print("Gist updated successfully!")
        else:
            print(f"Error: {response.status}")

if __name__ == "__main__":
    update()
