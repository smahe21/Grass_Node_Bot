import asyncio
import random
import ssl
import json
import time
import uuid
from loguru import logger
from websockets_proxy import Proxy, proxy_connect
from fake_useragent import UserAgent

# Creating an instance of UserAgent to generate random user agents
user_agent = UserAgent()

async def connect_to_wss(socks5_proxy, user_id, user_agent_string):
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, socks5_proxy))
    logger.info(device_id)
    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 10)
            custom_headers = {
                "User-Agent": user_agent_string
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = "wss://proxy.wynd.network:4650/"
            server_hostname = "proxy.wynd.network"
            proxy = Proxy.from_url(socks5_proxy)
            async with proxy_connect(uri, proxy=proxy, ssl=ssl_context, server_hostname=server_hostname,
                                     extra_headers=custom_headers) as websocket:
                async def send_ping():
                    while True:
                        send_message = json.dumps(
                            {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                        logger.debug(send_message)
                        await websocket.send(send_message)
                        await asyncio.sleep(20)

                await asyncio.sleep(1)
                asyncio.create_task(send_ping())

                while True:
                    response = await websocket.recv()
                    message = json.loads(response)
                    logger.info(message)
                    if message.get("action") == "AUTH":
                        auth_response = {
                            "id": message["id"],
                            "origin_action": "AUTH",
                            "result": {
                                "browser_id": device_id,
                                "user_id": user_id,
                                "user_agent": custom_headers['User-Agent'],
                                "timestamp": int(time.time()),
                                "device_type": "extension",
                                "version": "2.5.0"
                            }
                        }
                        logger.debug(auth_response)
                        await websocket.send(json.dumps(auth_response))

                    elif message.get("action") == "PONG":
                        pong_response = {"id": message["id"], "origin_action": "PONG"}
                        logger.debug(pong_response)
                        await websocket.send(json.dumps(pong_response))
        except Exception as e:
            logger.error(e)
            logger.error(socks5_proxy)


async def main():

    ## Get user id by calling this
    ## https://api.getgrass.io/retrieveUserSettings
    _user_id = 'REPLACE WITH USER ID'
    socks5_proxy_list = [

############ ADD SOCKS5 PROXIES HERE
#### COMMA SEPERATED LIST
    ##'socks5://grass-_crPFzKzCKo:asrEAsjd@proxy.com:12345',
    ##'socks5://grass-_crPFzKzCKo:dffdAAs@proxy.com:12345',


    ]
    # Generate random user agents for each proxy
    random_user_agents = [user_agent.random for _ in range(len(socks5_proxy_list))]
    tasks = [asyncio.ensure_future(connect_to_wss(proxy, _user_id, ua)) for proxy, ua in zip(socks5_proxy_list, random_user_agents)]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())

