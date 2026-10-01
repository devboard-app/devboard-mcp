from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    WORK_URL: str
    CORE_URL: str
    HTTP_TIMEOUT: int
    PUBLIC_URL: str = "http://localhost:18009"

settings = Settings()  # type: ignore
