from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    SN_INSTANCE: str

    SN_USERNAME: str

    SN_PASSWORD: str

    DATABASE_URL: str

    class Config:
        env_file = ".env"


settings = Settings()