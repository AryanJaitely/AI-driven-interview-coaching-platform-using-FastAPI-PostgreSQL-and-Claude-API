import asyncio
from app.db.database import init_db

async def main():
    await init_db()
    print("✅ All tables created!")

asyncio.run(main())