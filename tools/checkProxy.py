import json
import time

from aiohttp_socks import ProxyConnector
import aiohttp
class ProxyChecker:

    async def check_proxy(self, proxy_str):
        proxy = self.parse_proxy(proxy_str)

        connector = ProxyConnector.from_url(f'{proxy["type"]}://{(proxy["username"] + ":" + proxy["password"] + "@" if "password" in proxy else "")}{proxy["addr"]}',
                                            limit=200,
                                            limit_per_host=200,
                                            force_close=True,
                                            enable_cleanup_closed=True,
                                            verify_ssl=False)

        try:
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get('https://api.ipify.org?format=json', timeout=5) \
                        as response:
                    ip = json.loads(await response.text())["ip"]

                async with session.get(
                        f'http://www.geoplugin.net/json.gp?{ip}',
                        timeout=5
                ) as response:
                    country = json.loads(
                        await response.text()
                    )[
                        'geoplugin_countryName'
                    ]

                start_time_stamp = time.time()

                async with session.get("http://httpbin.org/ip", timeout=5):
                    await session.close()

                ping = round((time.time() - start_time_stamp) * 1000)
                return f"Прокси — (Задержка: {ping} ms, IP-Адрес: {ip}), страна: {country}) сохранены\nЕсли процесс запущен, перезапустите его."
        except Exception as e:
            print(e)
            return False

    def parse_proxy(self, proxy_str):
        proxy_params = proxy_str.split(';')

        proxy = {
            'type': proxy_params[0],
            'addr': proxy_params[1] + ':' + proxy_params[2]
        }
        if len(proxy_params) == 4:
            proxy['username'] = proxy_params[3]
        elif len(proxy_params) > 4:
            proxy['username'] = proxy_params[3]
            proxy['password'] = proxy_params[4]
        return proxy
