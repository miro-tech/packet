import os
import json
import urllib.request
from datetime import datetime, timedelta, timezone

GIST_ID = "5d53a0965ad16d964c5fb366e11532ff"
DOWNLOAD_TOKEN = "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"
GIST_TOKEN = os.getenv("GIST_TOKEN")
SOURCE_URL = "https://raw.githubusercontent.com/Roadlux/PacketVPN1.5.3-NEW/main/configInfo"

def update():
    # Шаг 1: Скачиваем конфиги
    req = urllib.request.Request(SOURCE_URL, headers={"Authorization": f"token {DOWNLOAD_TOKEN}"})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
    
    # Шаг 2: Извлекаем строки
    configs = [c['config']['stringServer'] for c in data['configs']]
    
    # --- ДОБАВЛЕНИЕ ВРЕМЕНИ (УРАЛ, UTC+5) ---
    ural_offset = timezone(timedelta(hours=5))
    ural_time = datetime.now(ural_offset).strftime('%d.%m.%Y %H:%M:%S')
    header_line = f"vless://00000000-0000-0000-0000-000000000000@127.0.0.1:0?type=none#🕒_Update_Ural:_{ural_time}"
    
    # Добавляем в начало списка
    configs.insert(0, header_line)
    # ----------------------------------------
    
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
