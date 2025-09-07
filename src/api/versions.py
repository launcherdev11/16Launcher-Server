from fastapi import APIRouter, HTTPException, Depends
from minecraft_launcher_lib.utils import get_version_list

from ..dependencies import get_database

router = APIRouter()


async def get_cached_versions(db):
    """
    Получить список версий из кэша или загрузить заново
    """
    cached_versions = await db.get_cached_versions()
    if cached_versions:
        return cached_versions

    versions = get_version_list()
    await db.cache_versions(versions)
    return versions


@router.get("/versions/vanilla")
async def version_list(db=Depends(get_database)):
    try:
        versions = await get_cached_versions(db)
        return versions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get versions: {str(e)}")


@router.get("/versions/vanilla/all")
async def version_all_list(db=Depends(get_database)):
    try:
        versions = await get_cached_versions(db)
        return [version['id'] for version in versions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get versions id: {str(e)}")


@router.get("/versions/vanilla/release")
async def release_list(db=Depends(get_database)):
    try:
        versions = await get_cached_versions(db)
        return [version['id'] for version in versions if version['type'] == 'release']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get release versions: {str(e)}")


@router.get("/versions/vanilla/snapshot")
async def snapshot_list(db=Depends(get_database)):
    try:
        versions = await get_cached_versions(db)
        return [version['id'] for version in versions if version['type'] == 'snapshot']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get snapshot versions: {str(e)}")


@router.get("/versions/vanilla/old_alpha")
async def alpha_list(db=Depends(get_database)):
    try:
        versions = await get_cached_versions(db)
        return [version['id'] for version in versions if version['type'] == 'old_alpha']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alpha versions: {str(e)}")


@router.get("/versions/vanilla/old_beta")
async def beta_list(db=Depends(get_database)):
    try:
        versions = await get_cached_versions(db)
        return [version['id'] for version in versions if version['type'] == 'old_beta']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get beta versions: {str(e)}")
