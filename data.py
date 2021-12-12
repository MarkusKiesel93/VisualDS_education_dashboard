import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).parent / 'data'


def get_europe_countries():
    COUNTRIES_PATH = DATA_PATH / 'europe_countries.csv'

    return pd.read_csv(COUNTRIES_PATH)


def get_education_data():
    WORLD_BANK_EDUCATION_PATH = DATA_PATH / 'world_bank' / 'API_4_DS2_en_csv_v2_3160069.csv'

    df = pd.read_csv(WORLD_BANK_EDUCATION_PATH, skiprows=4)

    df = df.drop(columns=['Unnamed: 65', 'Indicator Name', 'Country Name'])
    df = df.rename(columns={
        'Country Code': 'country_code',
        'Country Name': 'country_name',
        'Indicator Code': 'indicator_code',
        'Indicator Name': 'indicator_name',
    })

    df = df.melt(id_vars=['country_code', 'indicator_code'], var_name='year')
    df.year = df.year.astype(int)
    df = df.pivot(index=['country_code', 'year'], columns='indicator_code', values='value')

    # assert set(europe_countries.country_code3) == set(df.index.get_level_values('country_code'))
    # assert set([str(year) for year in range(1991,2021)]) == set(df.columns)

    return df


def get_hlo_data():
    WORLD_BANK_HLO_PATH = DATA_PATH / 'world_bank' / 'hlo_database.xlsx'

    df = pd.read_excel(WORLD_BANK_HLO_PATH, sheet_name='HLO Database')
    df = df.drop(columns=['country', 'sourcetest', 'n_res', 'hlo_se', 'hlo_m_se', 'hlo_f_se', 'region', 'incomegroup'])
    df = df.rename(columns={'code': 'country_code'})
    df = df.set_index(['country_code', 'year', 'subject', 'level'])
    df = df.groupby(['country_code', 'year']).mean()

    return df


def get_gdp_data():
    MADDISON_GDP_PATH = DATA_PATH / 'maddison' / 'mpd2020.xlsx'

    df = pd.read_excel(MADDISON_GDP_PATH, sheet_name='Full data')
    df = df.drop(columns=['pop', 'country'])
    df = df.rename(columns={'countrycode': 'country_code'})
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
