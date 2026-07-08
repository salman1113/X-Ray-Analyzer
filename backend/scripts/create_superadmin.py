import asyncio
import sys

from motor.motor_asyncio import AsyncIOMotorClient


async def main():
    email = (
        sys.argv[1]
        if len(sys.argv) > 1
        else input("Enter user's email to make Super Admin: ")
    )
    from core.settings import settings

    client = AsyncIOMotorClient(settings.DATABASE_URL)
    db = client[settings.DB_NAME]

    user = await db.users.find_one({"email": email})
    if not user:
        print(f"Error: User {email} not found in database.")
        return

    await db.users.update_one({"email": email}, {"$set": {"role": "superadmin"}})
    print(f"Success! {email} has been promoted to 'superadmin'.")


if __name__ == "__main__":
    asyncio.run(main())
