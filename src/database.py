import logging
from datetime import datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)


class MongoDB:
    def __init__(self):
        self.client: AsyncIOMotorClient | None = None
        self.db = None

    async def connect(self, connection_string: str | None = None):
        """Подключение к MongoDB"""
        try:
            if connection_string is None:
                connection_string = "mongodb://localhost:27017/launcherdb"

            self.client = AsyncIOMotorClient(connection_string)
            self.db = self.client.get_database("launcherdb")

            await self._create_indexes()

            logger.info("Successfully connected to MongoDB")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def _create_indexes(self):
        """Создание индексов для оптимизации запросов"""
        await self.db.versions.create_index("version_id", unique=True)
        await self.db.versions.create_index("type")
        await self.db.versions.create_index("releaseTime")

        await self.db.mods.create_index("mod_id", unique=True)
        await self.db.mods.create_index("name")
        await self.db.mods.create_index("minecraft_version")
        await self.db.mods.create_index("mod_loader")

        await self.db.cache.create_index("key", unique=True)
        await self.db.cache.create_index("expires_at", expireAfterSeconds=0)

    async def disconnect(self):
        """Отключение от MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def cache_versions(self, versions: list[dict[str, Any]]):
        """Кэширование списка версий Minecraft"""
        try:
            # Очищаем старые данные
            await self.db.versions.delete_many({})

            if versions:
                await self.db.versions.insert_many(versions)

            logger.info(f"Cached {len(versions)} Minecraft versions")
            return True

        except Exception as e:
            logger.error(f"Failed to cache versions: {e}")
            return False

    async def get_cached_versions(self) -> list[dict[str, Any]]:
        """Получение кэшированных версий"""
        try:
            cursor = self.db.versions.find().sort("releaseTime", -1)
            versions = await cursor.to_list(length=None)
            return versions
        except Exception as e:
            logger.error(f"Failed to get cached versions: {e}")
            return []

    async def get_versions_by_type(self, version_type: str) -> list[str]:
        """Получение версий по типу (release/snapshot)"""
        try:
            cursor = self.db.versions.find(
                {"type": version_type},
                {"_id": 0, "id": 1}
            )
            versions = await cursor.to_list(length=None)
            return [v["id"] for v in versions]
        except Exception as e:
            logger.error(f"Failed to get {version_type} versions: {e}")
            return []

    async def cache_mods_search(self, search_type: str, data: list[dict[str, Any]]) -> bool:
        """Кэширование результатов поиска модов"""
        try:
            await self.db.mods_cache.update_one(
                {"search_type": search_type},
                {"$set": {
                    "data": data,
                    "cached_at": datetime.utcnow(),
                    "expires_at": datetime.utcnow().timestamp() + 3600  # 1 час
                }},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to cache mods search: {e}")
            return False

    async def get_cached_mods_search(self, search_type: str) -> list[dict[str, Any]] | None:
        """Получение кэшированных результатов поиска модов"""
        try:
            cache = await self.db.mods_cache.find_one({"search_type": search_type})
            if cache and cache.get("expires_at", 0) > datetime.utcnow().timestamp():
                return cache.get("data", [])
            return None
        except Exception as e:
            logger.error(f"Failed to get cached mods search: {e}")
            return None

    async def cache_quilt_versions(self, mc_version: str, versions: list[dict[str, Any]]):
        """Кэширование версий Quilt"""
        try:
            await self.db.quilt_versions.update_one(
                {"minecraft_version": mc_version},
                {"$set": {
                    "versions": versions,
                    "cached_at": datetime.utcnow(),
                    "expires_at": datetime.utcnow().timestamp() + 3600  # 1 час
                }},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to cache Quilt versions: {e}")
            return False

    async def get_cached_quilt_versions(self, mc_version: str) -> list[dict[str, Any]] | None:
        """Получение кэшированных версий Quilt"""
        try:
            cache = await self.db.quilt_versions.find_one({"minecraft_version": mc_version})
            if cache and cache.get("expires_at", 0) > datetime.utcnow().timestamp():
                return cache.get("versions", [])
            return None
        except Exception as e:
            logger.error(f"Failed to get cached Quilt versions: {e}")
            return None

    # Общие методы для кэширования
    async def set_cache(self, key: str, data: Any, ttl: int = 3600) -> bool:
        """Установка значения в кэш"""
        try:
            await self.db.cache.update_one(
                {"key": key},
                {"$set": {
                    "data": data,
                    "expires_at": datetime.utcnow().timestamp() + ttl
                }},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to set cache for key {key}: {e}")
            return False

    async def get_cache(self, key: str) -> Any | None:
        try:
            cache = await self.db.cache.find_one({"key": key})
            if cache and cache.get("expires_at", 0) > datetime.utcnow().timestamp():
                return cache.get("data")
            return None
        except Exception as e:
            logger.error(f"Failed to get cache for key {key}: {e}")
            return None

    async def delete_cache(self, key: str) -> bool:
        """Удаление значения из кэша"""
        try:
            await self.db.cache.delete_one({"key": key})
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache for key {key}: {e}")
            return False
