import os
import json
import urllib.request

GIST_ID = "5d53a0965ad16d964c5fb366e11532ff"
DOWNLOAD_TOKEN = "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"
GIST_TOKEN = os.getenv("GIST_TOKEN")
SOURCE_URL = "https://raw.githubusercontent.com/Roadlux/PacketVPN1.5.3-NEW/main/configInfo"

def update():
    # Шаг 1: Скачиваем конфиги (аналог curl)
    req = urllib.request.Request(SOURCE_URL, headers={"Authorization": f"token {DOWNLOAD_TOKEN}"})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
    
    # Шаг 2: Извлекаем строки (аналог jq -r '.configs[].config.stringServer')
    configs = [c['config']['stringServer'] for c in data['configs']]
    content = "\n".join(configs)
    
    # Шаг 3: Отправляем в Gist (аналог вашего предыдущего метода)
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
