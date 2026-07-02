import os
import json
import urllib.request
import urllib.parse
import base64
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
    
    configs = []
    
    # Добавляем информационный заголовок с временем обновления
    ural_offset = timezone(timedelta(hours=5))
    ural_time = datetime.now(ural_offset).strftime('%d.%m.%Y %H:%M:%S')
    header_line = f"vless://00000000-0000-0000-0000-000000000000@127.0.0.1:0?type=none#🕒_Update_Ural:_{ural_time}"
    configs.append(header_line)
    
    # Шаг 2: Извлекаем fragmentServer и формируем ссылки
    configs_list = data.get('configs', [])
    
    for idx, c in enumerate(configs_list):
        fs = c.get('config', {}).get('fragmentServer')
        if fs:
            # Выводим структуру первого объекта в консоль Termux для визуального контроля
            if idx == 0:
                print("--- СТРУКТУРА ВАШЕГО fragmentServer (ДЛЯ ОТЛАДКИ) ---")
                print(json.dumps(fs, indent=2))
                print("-----------------------------------------------------")

            # Пробуем разные варианты названий ключей, которые могут быть в JSON
            addr = fs.get('server') or fs.get('address') or fs.get('host') or '127.0.0.1'
            port = fs.get('port') or 443
            uuid = fs.get('uuid') or fs.get('id') or fs.get('password') or '00000000-0000-0000-0000-000000000000'
            
            # Извлекаем транспортные протоколы и общие параметры, если они есть
            net_type = fs.get('network') or fs.get('type') or 'tcp'
            security = fs.get('security') or 'none'
            sni = fs.get('sni') or ''
            path = fs.get('path') or ''
            
            # Строим дополнительные параметры (Query параметры)
            query_params = {
                "type": net_type,
                "security": security
            }
            if sni:
                query_params["sni"] = sni
            if path:
                query_params["path"] = path
                
            query_string = urllib.parse.urlencode(query_params)
            
            # Имя профиля в Nekobox
            name = f"Proxy_{addr}_{port}"
            
            # Собираем готовую VLESS строку
            link = f"vless://{uuid}@{addr}:{port}?{query_string}#{urllib.parse.quote(name)}"
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
