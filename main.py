from fastapi import FastAPI
from app.database.database import connect
from app.routers.router_websocket import user_router_websocket
from app.routers.routers_user import user_router_user

app = FastAPI(title="Chat API", docs_url="/docs")
app.include_router(user_router_user)
app.include_router(user_router_websocket)


@app.on_event("startup")
async def startup():
    await connect()
