from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    WORK_URL: str
    HTTP_TIMEOUT: int


settings = Settings()  # type: ignore
