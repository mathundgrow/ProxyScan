
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

PROXY_LIST_URL = "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt"
CHECK_URL = "https://api.ipify.org"

MAX_LATENCY = 1000
MAX_WORKERS = 20

PROXY_FILE = "working_proxies.txt"
REPORT_FILE = "proxy_report.txt"


def get_proxies():
    response = requests.get(PROXY_LIST_URL, timeout=15)
    response.raise_for_status()

    return response.text.splitlines()


def get_real_ip():
    response = requests.get(CHECK_URL, timeout=10)
    response.raise_for_status()

    return response.text.strip()


def check_proxy(proxy):
    proxy_url = f"socks5h://{proxy}"

    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }

    try:
        start_time = time.perf_counter()

        response = requests.get(
            CHECK_URL,
            proxies=proxies,
            timeout=8
        )

        latency = (time.perf_counter() - start_time) * 1000

        response.raise_for_status()

        external_ip = response.text.strip()

        return {
            "ip": external_ip,
            "latency": round(latency)
        }

    except requests.RequestException:
        return None


def get_geo_info(ip):
    url = f"http://ip-api.com/json/{ip}"

    params = {
        "fields": "status,message,country,countryCode,city,isp"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data["status"] != "success":
            return None

        return {
            "country": data["country"],
            "country_code": data["countryCode"],
            "city": data["city"],
            "isp": data["isp"]
        }

    except (requests.RequestException, ValueError, KeyError):
        return None


def main():
    proxies = get_proxies()
    real_ip = get_real_ip()

    print(f"Получено прокси: {len(proxies)}")
    print(f"Твой реальный IP: {real_ip}")
    print(f"Количество потоков: {MAX_WORKERS}")
    print("-" * 40)

    working_count = 0
    completed_count = 0

    with open(PROXY_FILE, "w", encoding="utf-8") as proxy_file, \
        open(REPORT_FILE, "w", encoding="utf-8") as report_file:

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

            futures = {
                executor.submit(check_proxy, proxy): proxy
                for proxy in proxies
            }

            for future in as_completed(futures):
                proxy = futures[future]
                completed_count += 1

                print(
                    f"\n[{completed_count}/{len(proxies)}] "
                    f"Проверяем результат {proxy}..."
                )

                try:
                    result = future.result()
                except Exception as error:
                    print(f"[-] Ошибка: {error}")
                    continue

                if result is None:
                    print("[-] Не работает")
                    continue

                external_ip = result["ip"]
                latency = result["latency"]

                if external_ip == real_ip:
                    print("[-] IP не изменился!")
                    continue

                if latency > MAX_LATENCY:
                    print(f"[-] Слишком медленный: {latency} ms")
                    continue

                geo_info = get_geo_info(external_ip)

                time.sleep(1.4)

                if geo_info is None:
                    print("[-] Не удалось определить страну")
                    continue

                if geo_info["country_code"] == "RU":
                    print("[-] Россия. Прокси отклонён")
                    continue

                proxy_file.write(f"{proxy}\n")
                proxy_file.flush()

                report_file.write(
                    f"Proxy: {proxy}\n"
                    f"External IP: {external_ip}\n"
                    f"Country: {geo_info['country']}\n"
                    f"Country code: {geo_info['country_code']}\n"
                    f"City: {geo_info['city']}\n"
                    f"ISP: {geo_info['isp']}\n"
                    f"Latency: {latency} ms\n"
                    f"{'-' * 40}\n"
                )
                report_file.flush()

                working_count += 1

                print("[+] Подходит!")
                print(f"    IP: {external_ip}")
                print(f"    Страна: {geo_info['country']}")
                print(f"    Город: {geo_info['city']}")
                print(f"    Провайдер: {geo_info['isp']}")
                print(f"    Задержка: {latency} ms")

    print("\n" + "-" * 40)
    print(f"Подходящих прокси: {working_count}")
    print(f"Прокси сохранены в: {PROXY_FILE}")
    print(f"Отчёт сохранён в: {REPORT_FILE}")


if __name__ == "__main__":
    main()
