from fastapi import FastAPI

from api.routes import router


app = FastAPI(
    title="DB Fix Agent",
    version="1.0"
)

app.include_router(router)