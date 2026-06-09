import os
import json
import urllib.request

# Конфигурация
GIST_ID = "5d53a0965ad16d964c5fb366e11532ff"
GITHUB_TOKEN = os.getenv("GIST_TOKEN")
SOURCE_URL = "https://raw.githubusercontent.com/Roadlux/PacketVPN1.5.3-NEW/main/configInfo"

def update():
    # 1. Скачиваем данные
    with urllib.request.urlopen(SOURCE_URL) as response:
        data = json.loads(response.read().decode())
    
    # 2. Формируем строку
    configs = [c['config']['stringServer'] for c in data['configs']]
    content = "\n".join(configs)
    
    # 3. Отправляем в Gist
    payload = {
        "files": {
            "sub.txt": {"content": content}
        }
    }
    
    req = urllib.request.Request(
        f"https://api.github.com/gists/{GIST_ID}",
        data=json.dumps(payload).encode('utf-8'),
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        },
        method="PATCH"
    )
    
    with urllib.request.urlopen(req) as response:
        print("Gist updated successfully!")

if __name__ == "__main__":
    update()
