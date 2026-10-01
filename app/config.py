from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    WORK_URL: str
    CORE_URL: str
    HTTP_TIMEOUT: int
    PUBLIC_URL: str = "http://localhost:18009"
    REDIS_URL: str
    AUTH_URL: str
    JWT_SECRET: str
    REFRESH_TOKEN_TTL_DAYS: int = 7

settings = Settings()  # type: ignore
