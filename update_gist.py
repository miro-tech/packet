import os
import json
import requests

# Конфигурация
GIST_ID = "5d53a0965ad16d964c5fb366e11532ff"
# Токен для скачивания (тот самый, который вы указали)
DOWNLOAD_TOKEN = "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"
# Токен для обновления Gist (из ваших Secrets)
GIST_TOKEN = os.getenv("PACKETTOKEN")

SOURCE_URL = "https://raw.githubusercontent.com/Roadlux/PacketVPN1.5.3-NEW/main/configInfo"

def update():
    # 1. Скачиваем данные из репозитория
    print("Скачивание данных...")
    headers = {"Authorization": f"token {DOWNLOAD_TOKEN}"}
    response = requests.get(SOURCE_URL, headers=headers)
    
    if response.status_code != 200:
        print(f"Ошибка скачивания: {response.status_code} - {response.text}")
        return

    # 2. Обработка JSON и извлечение VLESS строк
    data = response.json()
    configs = [c['config']['stringServer'] for c in data['configs']]
    content = "\n".join(configs)
    
    # 3. Обновление Gist
    print("Обновление Gist...")
    gist_headers = {
        "Authorization": f"token {GIST_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "files": {
            "sub.txt": {"content": content}
        }
    }
    
    gist_response = requests.patch(
        f"https://api.github.com/gists/{GIST_ID}",
        headers=gist_headers,
        json=payload
    )
    
    if gist_response.status_code == 200:
        print("Gist успешно обновлен!")
    else:
        print(f"Ошибка обновления Gist: {gist_response.status_code}")
        print(gist_response.text)

if __name__ == "__main__":
    update()
