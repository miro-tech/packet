import os
import json
import urllib.request
import base64

# Конфигурация
GIST_ID = "5d53a0965ad16d964c5fb366e11532ff"
GITHUB_TOKEN = os.getenv("GIST_TOKEN")

# URL для получения файла через GitHub API
# Если репозиторий чужой, убедитесь, что токен имеет права доступа к нему
FILE_API_URL = "https://api.github.com/repos/Roadlux/PacketVPN1.5.3-NEW/contents/configInfo"
GIST_API_URL = f"https://api.github.com/gists/{GIST_ID}"

def update():
    # 1. Скачиваем данные файла через API
    req_get = urllib.request.Request(
        FILE_API_URL,
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
    )
    
    with urllib.request.urlopen(req_get) as response:
        file_data = json.loads(response.read().decode())
