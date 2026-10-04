#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone


# ====================== НАСТРОЙКИ ======================

# Публичный источник JSON
SOURCE_URL = "https://api.npoint.io/18c7fa1acf6cf9f22bea"

# Gist
GIST_ID = "5d53a0965ad16d964c5fb366e11532ff"
GIST_TOKEN = os.getenv("GIST_TOKEN")

# ========================================================


def get_source_data(url: str) -> dict:
    """Скачивает публичный JSON без каких-либо секретов."""

    print(f"Запрашиваю источник: {url}")

    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Config-Updater"
        }
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")

    print(f"Получено: {len(raw)} байт")

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print("Ответ источника:")
        print(raw[:2000])
        raise Exception(f"Источник вернул некорректный JSON: {e}")


def make_vless_kcp(
    address,
    port,
    uuid,
    seed=None,
    header_type="dns",
    domain=None,
    encryption="none",
    remark=""
):
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

    return (
        f"vless://{uuid}@{address}:{port}"
        f"?{query}"
        f"#{urllib.parse.quote(remark)}"
    )


def make_trojan_xhttp(
    address,
    port,
    password,
    host,
    path="/html",
    security="tls",
    sni=None,
    fp="chrome",
    alpn="h2",
    remark=""
):
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

    return (
        f"trojan://{password}@{address}:{port}"
        f"?{query}"
        f"#{urllib.parse.quote(remark)}"
    )


def extract_link(conf: dict, remark: str):
    """Достаёт ссылку из fragmentServer."""

    proxy = None

    # Сначала ищем outbound с tag=proxy
    for ob in conf.get("outbounds", []):
        if ob.get("tag") == "proxy":
            proxy = ob
            break

    # Если proxy нет — ищем первый VLESS/Trojan
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

    # ====================================================
    # VLESS + KCP
    # ====================================================

    if protocol == "vless" and network == "kcp":

        try:
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

        except (KeyError, IndexError, TypeError) as e:
            print(f"[!] Ошибка VLESS KCP ({remark}): {e}")
            return None

    # ====================================================
    # Trojan + XHTTP
    # ====================================================

    elif protocol == "trojan" and network == "xhttp":

        try:
            server = proxy["settings"]["servers"][0]

            xhttp = stream.get("xhttpSettings", {})
            tls = stream.get("tlsSettings", {})

            alpn_list = tls.get("alpn")

            if alpn_list:
                alpn = ",".join(alpn_list)
            else:
                alpn = "h2"

            return make_trojan_xhttp(
                address=server["address"],
                port=server["port"],
                password=server["password"],
                host=xhttp.get("host", ""),
                path=xhttp.get("path", "/"),
                security=stream.get("security", "none"),
                sni=tls.get("serverName"),
                fp=tls.get("fingerprint", "chrome"),
                alpn=alpn,
                remark=remark
            )

        except (KeyError, IndexError, TypeError) as e:
            print(f"[!] Ошибка Trojan XHTTP ({remark}): {e}")
            return None

    return None


def update():

    # ====================================================
    # 1. Получаем JSON из npoint
    # ====================================================

    data = get_source_data(SOURCE_URL)

    if not isinstance(data, dict):
        raise Exception("Источник не является JSON-объектом")

    configs_data = data.get("configs")

    if not isinstance(configs_data, list):
        raise Exception(
            "В JSON отсутствует массив 'configs'"
        )

    print(f"Конфигураций в источнике: {len(configs_data)}")

    configs = []

    # ====================================================
    # 2. Временная метка UTC+5
    # ====================================================

    ural_offset = timezone(timedelta(hours=5))

    ural_time = datetime.now(ural_offset).strftime(
        "%d.%m.%Y %H:%M:%S"
    )

    configs.append(
        "vless://00000000-0000-0000-0000-000000000000"
        "@127.0.0.1:0?type=none"
        f"#🕒_Update:_{urllib.parse.quote(ural_time)}"
    )

    # ====================================================
    # 3. Обрабатываем конфиги
    # ====================================================

    for index, c in enumerate(configs_data):

        if not isinstance(c, dict):
            print(f"[!] Пропуск элемента #{index}: не объект")
            continue

        name = c.get("countryName", "Proxy")

        config = c.get("config", {})

        if not isinstance(config, dict):
            print(f"[!] {name}: config не является объектом")
            continue

        config_type = config.get("configType")

        # ------------------------------------------------
        # Уже готовая ссылка
        # ------------------------------------------------

        if config_type == "string":

            link = config.get("stringServer")

            if link:

                if "#" not in link:
                    link = (
                        f"{link}#"
                        f"{urllib.parse.quote(str(name))}"
                    )

                configs.append(link)

                print(f"[+] {name}: готовая ссылка")

            else:
                print(f"[-] {name}: stringServer отсутствует")

            continue

        # ------------------------------------------------
        # Fragment → генерируем ссылку
        # ------------------------------------------------

        if config_type == "fragment":

            fs = config.get("fragmentServer", {})

            if not isinstance(fs, dict):
                print(
                    f"[-] {name}: fragmentServer не объект"
                )
                continue

            link = extract_link(fs, str(name))

            if link:
                configs.append(link)
                print(f"[+] {name}: ссылка сгенерирована")
            else:
                print(
                    f"[-] {name}: неподдерживаемый fragment"
                )

            continue

        print(
            f"[-] {name}: неизвестный configType={config_type}"
        )

    # ====================================================
    # 4. Формируем подписку
    # ====================================================

    content = "\n".join(configs)

    print()
    print(
        f"Сгенерировано ссылок: {len(configs) - 1}"
    )

    # ====================================================
    # 5. Проверяем Gist token
    # ====================================================

    if not GIST_TOKEN:
        raise Exception(
            "Не задан GIST_TOKEN "
            "(переменная окружения)"
        )

    # ====================================================
    # 6. Обновляем Gist
    # ====================================================

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
            "Accept": "application/vnd.github+json",
            "User-Agent": "Config-Updater"
        }
    )

    with urllib.request.urlopen(
        gist_req,
        timeout=30
    ) as response:

        if response.status == 200:
            print("Успешно обновлено в Gist!")
        else:
            print(
                f"Ошибка Gist: {response.status}"
            )


if __name__ == "__main__":
    update()
