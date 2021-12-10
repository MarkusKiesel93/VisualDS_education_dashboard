from pathlib import Path


class Settings():
    DATA_PATH = Path(__file__).parent / 'data'
    COUNTRIES_PATH = DATA_PATH / 'europe_countries.csv'
    WORLD_BANK_DATA_PATH = DATA_PATH / 'world_bank' / 'API_4_DS2_en_csv_v2_3160069.csv'


settings = Settings()
