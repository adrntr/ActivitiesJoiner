from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    DB_URL: str = ""
    TEST_DB_URL : str = ""
    ENVIRONMENT: str = ""

    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"))

    @property
    def database_url(self):
        if self.ENVIRONMENT == "development":
            return self.DB_URL
        elif self.ENVIRONMENT == "testing":
            return self.TEST_DB_URL
        else:
            raise ValueError("Invalid environment")



settings = Settings()


