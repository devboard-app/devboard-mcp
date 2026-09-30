from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    WORK_URL: str
    HTTP_TIMEOUT: int
    CORE_URL: str


settings = Settings()  # type: ignore
