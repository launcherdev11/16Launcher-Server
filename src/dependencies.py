from .database import MongoDB

bd = None


async def get_database() -> MongoDB:
    """Зависимость для получения экземпляра базы данных"""
    global bd
    if bd is None:
        bd = MongoDB()
        await bd.connect()
    return bd
