from pathlib import Path


class Settings():
    DATA_PATH = Path(__file__).parent / 'data'


settings = Settings()
