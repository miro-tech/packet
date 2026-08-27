#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

# ====================== НАСТРОЙКИ ======================

# Источник (приватный репозиторий)
GITHUB_TOKEN = "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"
GITHUB_REPO = "RoadLuxGroup/assets-1.5.3.2"
GITHUB_PATH = "data"
GITHUB_REF = "main"

# Gist
GIST_ID = "5d53a0965ad16d964c5fb366e11532ff"
GIST_TOKEN = os.getenv("GIST_TOKEN")   # лучше хранить в переменной окружения

# =======================================================


def get_private_github_file(token: str, repo: str, path: str, ref: str = "main") -> dict:
    """Скачивает JSON из приватного репозитория через GitHub API"""
    api_url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={ref}"
    
    print(f"Запрашиваю GitHub API: {api_url}")
    
    req = urllib.request.Request(api_url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Config-Updater"
    })
    
    with urllib.request.urlopen(req, timeout=20) as resp:
        meta = json.loads(resp.read().decode("utf-8"))
    
    download_url = meta.get("download_url")
    if not download_url:
        raise Exception("Не удалось получить download_url")
    
    print("Скачиваю файл...")
    req2 = urllib.request.Request(download_url, headers={"User-Agent": "Config-Updater"})
    with urllib.request.urlopen(req2, timeout=30) as resp2:
        return json.loads(resp2.read().decode("utf-8"))


def make_vless_kcp(address, port, uuid, seed=None, header_type="dns", domain=None, encryption="none", remark=""):
    params = {
        "encryption": encryption,
        "security": "none",
        "type": "kcp",
        "headerType": header_type,
    }
    if seed:
        params["seed"] = seed
    if domain:
        params["host"] = domain
    query = urllib.parse.urlencode(params)
    return f"vless://{uuid}@{address}:{port}?{query}#{urllib.parse.quote(remark)}"


def make_trojan_xhttp(address, port, password, host, path="/html", security="tls", sni=None, fp="chrome", alpn="h2", remark=""):
    params = {
        "security": security,
        "type": "xhttp",
        "path": path,
        "host": host,
        "mode": "auto",
    }
    if security == "tls":
        params["fp"] = fp
        params["alpn"] = alpn
        params["sni"] = sni or host
    query = urllib.parse.urlencode(params)
    return f"trojan://{password}@{address}:{port}?{query}#{urllib.parse.quote(remark)}"


def extract_link(conf: dict, remark: str) -> str | None:
    """Правильно достаёт ссылку из fragmentServer"""
    proxy = None
    for ob in conf.get("outbounds", []):
        if ob.get("tag") == "proxy":
            proxy = ob
            break
    if not proxy:
        for ob in conf.get("outbounds", []):
            if ob.get("protocol") in ("vless", "trojan"):
                proxy = ob
                break
    if not proxy:
        return None

    protocol = proxy.get("protocol")
    stream = proxy.get("streamSettings", {})
    network = stream.get("network", "")

    if protocol == "vless" and network == "kcp":
        vnext = proxy["settings"]["vnext"][0]
        user = vnext["users"][0]
        kcp = stream.get("kcpSettings", {})
        header = kcp.get("header", {})
        return make_vless_kcp(
            address=vnext["address"],
            port=vnext["port"],
            uuid=user["id"],
            seed=kcp.get("seed"),
            header_type=header.get("type", "none"),
            domain=header.get("domain"),
            encryption=user.get("encryption", "none"),
            remark=remark
        )

    elif protocol == "trojan" and network == "xhttp":
        server = proxy["settings"]["servers"][0]
        xhttp = stream.get("xhttpSettings", {})
        tls = stream.get("tlsSettings", {})
        return make_trojan_xhttp(
            address=server["address"],
            port=server["port"],
            password=server["password"],
            host=xhttp.get("host", ""),
            path=xhttp.get("path", "/"),
            security=stream.get("security", "none"),
            sni=tls.get("serverName"),
            fp=tls.get("fingerprint", "chrome"),
            alpn=",".join(tls.get("alpn", ["h2"])) if tls.get("alpn") else "h2",
            remark=remark
        )

    # fallback для простых string-конфигов
    return None


def update():
    # 1. Получаем данные
    data = get_private_github_file(GITHUB_TOKEN, GITHUB_REPO, GITHUB_PATH, GITHUB_REF)
    
    configs = []
    
    # 2. Временная метка (Урал, UTC+5)
    ural_offset = timezone(timedelta(hours=5))
    ural_time = datetime.now(ural_offset).strftime('%d.%m.%Y %H:%M:%S')
    configs.append(f"vless://00000000-0000-0000-0000-000000000000@127.0.0.1:0?type=none#🕒_Update:_{ural_time}")
    
    # 3. Обрабатываем все конфиги
    for c in data.get("configs", []):
        name = c.get("countryName", "Proxy")
        config_type = c.get("config", {}).get("configType")
        
        # Уже готовая ссылка
        if config_type == "string":
            link = c.get("config", {}).get("stringServer")
            if link:
                # Добавляем имя, если его нет
                if "#" not in link:
                    link = f"{link}#{urllib.parse.quote(name)}"
                configs.append(link)
            continue
        
        # Fragment → генерируем ссылку
        if config_type == "fragment":
            fs = c.get("config", {}).get("fragmentServer", {})
            link = extract_link(fs, name)
            if link:
                configs.append(link)
    
    content = "\n".join(configs)
    print(f"Сгенерировано ссылок: {len(configs) - 1}")  # минус временная метка
    
    # 4. Заливаем в Gist
    if not GIST_TOKEN:
        raise Exception("Не задан GIST_TOKEN (переменная окружения)")
    
    payload = json.dumps({
        "files": {
            "sub.txt": {
                "content": content
            }
        }
    }).encode("utf-8")
    
    gist_req = urllib.request.Request(
        f"https://api.github.com/gists/{GIST_ID}",
        data=payload,
        method="PATCH",
        headers={
            "Authorization": f"token {GIST_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "Config-Updater"
        }
    )
    
    with urllib.request.urlopen(gist_req) as response:
        if response.status == 200:
            print("Успешно обновлено в Gist!")
        else:
            print(f"Ошибка Gist: {response.status}")


if __name__ == "__main__":
    update()
