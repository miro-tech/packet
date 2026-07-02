import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

GIST_ID = "5d53a0965ad16d964c5fb366e11532ff"
GIST_TOKEN = os.getenv("GIST_TOKEN")
DOWNLOAD_TOKEN = "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"
SOURCE_URL = "https://raw.githubusercontent.com/Roadlux/assets-1.5.3.1/main/data"

def update():
    req = urllib.request.Request(SOURCE_URL, headers={"Authorization": f"token {DOWNLOAD_TOKEN}"})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
    
    configs = []
    
    # Добавляем временную метку в начало
    ural_offset = timezone(timedelta(hours=5))
    ural_time = datetime.now(ural_offset).strftime('%d.%m.%Y %H:%M:%S')
    configs.append(f"vless://00000000-0000-0000-0000-000000000000@127.0.0.1:0?type=none#🕒_Update:_{ural_time}")
    
    for c in data.get('configs', []):
        name = c.get('countryName', 'Proxy')
        fs = c.get('config', {}).get('fragmentServer', {})
        outbounds = fs.get('outbounds', [])
        proxy = next((o for o in outbounds if o.get('tag') == 'proxy'), None)
        
        if proxy:
            proto = proxy.get('protocol')
            
            if proto == 'trojan':
                svr = proxy.get('settings', {}).get('servers', [{}])[0]
                stream = proxy.get('streamSettings', {})
                reality = stream.get('realitySettings', {})
                xhttp = stream.get('xhttpSettings', {})
                
                # Собираем параметры для Reality
                params = {
                    "security": "reality",
                    "sni": reality.get('serverName'),
                    "fp": reality.get('fingerprint'),
                    "pbk": reality.get('publicKey'),
                    "sid": reality.get('shortId'),
                    "type": stream.get('network'),
                    "path": xhttp.get('path'),
                    "host": xhttp.get('host')
                }
                # Убираем None значения
                params = {k: v for k, v in params.items() if v}
                
                link = f"trojan://{svr.get('password')}@{svr.get('address')}:{svr.get('port')}?{urllib.parse.urlencode(params)}#{urllib.parse.quote(name)}"
                configs.append(link)
                
            elif proto == 'vless':
                vnext = proxy.get('settings', {}).get('vnext', [{}])[0]
                user = vnext.get('users', [{}])[0]
                net = proxy.get('streamSettings', {}).get('network', 'tcp')
                
                link = f"vless://{user.get('id')}@{vnext.get('address')}:{vnext.get('port')}?type={net}&security=none#{urllib.parse.quote(name)}"
                configs.append(link)

    content = "\n".join(configs)
    
    # Отправка в Gist
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
            print("Успешно обновлено!")
        else:
            print(f"Ошибка: {response.status}")

if __name__ == "__main__":
    update()
