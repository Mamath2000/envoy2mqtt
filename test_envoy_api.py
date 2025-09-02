import asyncio
from src.envoy_api import EnvoyAPI

async def main():
    api = EnvoyAPI(
        username="mathieu.beau@gmail.com",
        password="Nm4PKFCMNAjoWXKzdeF2jbf3QdsjnbjRrzWEfZvw3mg7vpKi",
        envoy_host="https://192.168.90.240",
        serial_number="122226051519"
    )
    await api.authenticate()

if __name__ == "__main__":
    asyncio.run(main())