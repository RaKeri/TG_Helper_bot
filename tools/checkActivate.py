import re

import requests
import hashlib
import platform
import uuid

def get_url():
    try:
        r = requests.get('https://pastebin.com/ZAY3MwB5')
    except Exception as e:
        raise Exception(f"Отсутвствует интернет подключение.")
    pattern = r"https?://[a-zA-Z0-9.-]+\.ngrok-free\.app"
    matches = re.findall(pattern, r.text)
    url = matches[0]
    return url


def download_update(url, version):
    try:
        response = requests.get(f"{get_url()}{url}")
        response.raise_for_status()
        new_script = f"update.rar"
        with open(new_script, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        return False



def checkUpdate(version):
    """Проверяет обновления на сервере."""
    try:
        response = requests.get(f"{get_url()}/check_update", params={"version": version})
        response.raise_for_status()
        data = response.json()
        if data["update"]:
            dw =download_update(data["url"], data["version"])
            if dw:
                return True
            else:
                return False
    except Exception as e:
        return False
    

def get_device_id():
    """Генерирует уникальный идентификатор устройства."""
    system_info = f"{platform.system()}-{platform.node()}-{platform.processor()}-{uuid.getnode()}"
    return hashlib.sha256(system_info.encode()).hexdigest()

def register_device(device_id):
    """Регистрирует устройство на сервере."""
    response = requests.post(f"{get_url()}/register_device", json={"device_id": device_id})

def check_license(device_id):
    """Проверяет лицензию устройства на сервере."""
    response = requests.post(f"{get_url()}/check_license", json={"device_id": device_id})
    result = response.json()
    status = result.get("status")
    if status == "active":
        return result.get("time")
    elif status == "expired":
        print("Лицензия истекла.")
    elif status == "not_found":
        print("Срок действия лицензии истек.")
        register_device(device_id)
    return False
