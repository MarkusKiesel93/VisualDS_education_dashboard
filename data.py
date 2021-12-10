import pandas as pd

from config import settings
from countries import europe_countries


def get_world_bank_data():
    df = pd.read_csv(settings.DATA_PATH / 'world_bank' / 'API_4_DS2_en_csv_v2_3160069.csv', skiprows=4)
    years_to_remove = [str(year) for year in range(1960, 1991)]
    columns_to_remove = ['Unnamed: 65', 'Indicator Name', 'Country Name'] + years_to_remove
    df = df.drop(columns=columns_to_remove)
    df = df.rename(columns={
        'Country Code': 'country_code',
        'Country Name': 'country_name',
        'Indicator Code': 'indicator_code',
        'Indicator Name': 'indicator_name',
    })
    df = df[df.country_code.isin(europe_countries.country_code3)]
    df = df.set_index(['country_code', 'indicator_code'])

    assert set(europe_countries.country_code3) == set(df.index.get_level_values('country_code'))
    assert set([str(year) for year in range(1991,2021)]) == set(df.columns)

    return df


if __name__ == '__main__':
    df = get_world_bank_data()
    print(df.shape)
    print(df.head())
    
