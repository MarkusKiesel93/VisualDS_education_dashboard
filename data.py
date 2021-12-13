import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).parent / 'data'


def get_europe_countries():
    COUNTRIES_PATH = DATA_PATH / 'europe_countries.csv'

    return pd.read_csv(COUNTRIES_PATH)


def get_selected_indicators():
    PATH = DATA_PATH / 'world_bank' / 'selected_indicators.csv'

    df = pd.read_csv(PATH)

    return df.indicator_code.values


def get_education_data():
    PATH = DATA_PATH / 'world_bank' / 'API_4_DS2_en_csv_v2_3160069.csv'

    df = pd.read_csv(PATH, skiprows=4)

    df = df.rename(columns={
        'Country Code': 'country_code',
        'Country Name': 'country_name',
        'Indicator Code': 'indicator_code'
    })

    countries = df[['country_code', 'country_name']].set_index('country_code').drop_duplicates()
    df = df.drop(columns=['Unnamed: 65', 'Indicator Name', 'country_name'])

    df = df.melt(id_vars=['country_code', 'indicator_code'], var_name='year')
    df.year = df.year.astype(int)
    df = df.pivot(index=['country_code', 'year'], columns='indicator_code', values='value')

    selected_indicators = get_selected_indicators()
    df = df[selected_indicators]
    df = df.join(countries, on='country_code')

    # assert set(europe_countries.country_code3) == set(df.index.get_level_values('country_code'))
    # assert set([str(year) for year in range(1991,2021)]) == set(df.columns)

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


def merged_data(europe=True):
    edu = get_education_data()
    hlo = get_hlo_data()

    df = edu.join(hlo)
    gdp = get_gdp_data()
    df = df.join(gdp)

    df = df.sort_index(axis=1, level='year')
    df = df.groupby('country_code').ffill()

    years_to_remove = [year for year in range(1960, 2001)]
    df = df.drop(index=years_to_remove, level='year')

    if europe:
        europe_countries = get_europe_countries()
        df = df[df.index.isin(europe_countries.country_code3, level='country_code')]

    return df


if __name__ == '__main__':
    df = merged_data()
    df.to_csv(DATA_PATH / 'data.csv')
