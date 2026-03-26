from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_users():
    return [{"id":1, "name": "Alex"}]
