import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as c:
        r = await c.post('http://127.0.0.1:8000/api/candidate/practice/start')
        print(r.status_code, r.text)

if __name__ == "__main__":
    asyncio.run(main())
