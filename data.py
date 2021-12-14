import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).parent / 'data'


def get_europe_countries():
    COUNTRIES_PATH = DATA_PATH / 'europe_countries.csv'

    return pd.read_csv(COUNTRIES_PATH)


def get_education_indicators(without_info=True):
    PATH = DATA_PATH / 'world_bank' / 'selected_indicators.csv'

    df = pd.read_csv(PATH)
    df = df.set_index('indicator_code')
    if without_info:
        df = df.indicator

    return df


def get_education_data():
    PATH = DATA_PATH / 'world_bank' / 'API_4_DS2_en_csv_v2_3160069.csv'

    df = pd.read_csv(PATH, skiprows=4)
    indicators = get_education_indicators()

    df = df.rename(columns={
        'Country Code': 'country_code',
        'Country Name': 'country_name',
        'Indicator Code': 'indicator_code'
    })

    countries = df[['country_code', 'country_name']].set_index('country_code').drop_duplicates()
    df = df.drop(columns=['Unnamed: 65', 'Indicator Name', 'country_name'])

    df = df.melt(id_vars=['country_code', 'indicator_code'], var_name='year')
    df.year = df.year.astype(int)
    df = df.join(indicators, on='indicator_code', how='right')
    df = df.drop(columns=['indicator_code'])
    df = df.pivot(index=['country_code', 'year'], columns='indicator', values='value')
    df = df.join(countries, on='country_code')

    return df


def get_indicator_desc():
    PATH = DATA_PATH / 'world_bank' / 'Metadata_Indicator_API_4_DS2_en_csv_v2_3160069.csv'

    df = pd.read_csv(PATH)
    df = df.drop(columns=['SOURCE_ORGANIZATION', 'Unnamed: 4'])
    df = df.rename(columns={'INDICATOR_CODE': 'indicator_code', 'INDICATOR_NAME': 'indicator_name'})
    df = df.set_index('indicator_code')

    return df


def get_hlo_data():
    PATH = DATA_PATH / 'world_bank' / 'hlo_database.xlsx'

    df = pd.read_excel(PATH, sheet_name='HLO Database')
    df = df.drop(columns=['country', 'sourcetest', 'n_res', 'hlo_se', 'hlo_m_se', 'hlo_f_se', 'region', 'incomegroup'])
    df = df.rename(columns={'code': 'country_code'})
    df = df.set_index(['country_code', 'year', 'subject', 'level'])
    df = df.groupby(['country_code', 'year']).mean()

    return df


def get_gdp_data():
    PATH = DATA_PATH / 'maddison' / 'mpd2020.xlsx'

    df = pd.read_excel(PATH, sheet_name='Full data')
    df = df.drop(columns=['country'])
    df = df.rename(columns={'countrycode': 'country_code', 'pop': 'population'})
    df = df.set_index(['country_code', 'year'])

    return df


def merged_data(from_year=2000, europe=False):
    edu = get_education_data()
    hlo = get_hlo_data()

    df = edu.join(hlo)
    gdp = get_gdp_data()
    df = df.join(gdp)

    df = df.sort_index(axis=1, level='year')
    df = df.groupby('country_code').ffill()

    df = df[df.index.isin([year for year in range(from_year, 2021)], level=1)]

    if europe:
        europe_countries = get_europe_countries()
        df = df[df.index.isin(europe_countries.country_code3, level='country_code')]

    return df


if __name__ == '__main__':
    df = merged_data()
    df.to_csv(DATA_PATH / 'data.csv')
