import pandas as pd
from pathlib import Path

from pandas.core.frame import DataFrame

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


def get_education_meta():
    PATH = DATA_PATH / 'world_bank' / 'Metadata_Country_API_4_DS2_en_csv_v2_3160069.csv'

    df = pd.read_csv(PATH)
    df = df.drop(columns=['Unnamed: 5', 'SpecialNotes'])
    df = df.rename(columns={
        'Country Code': 'country_code',
        'Region': 'region',
        'IncomeGroup': 'income_group',
        'TableName': 'country_name'
    })
    df = df.set_index('country_code')

    df = df[df.region.notna()]

    # only Venezuela income_group missing (online reseach suggests "Lower middle income")
    df.income_group = df.income_group.fillna('Lower middle income')

    return df


def create_indicator_levels(name):
    parts = name.split('_')

    school_level = ['primary', 'secondary', 'tertiary']
    gender = ['female', 'male', 'total']
    level1 = 'total'
    level2 = 'total'

    if len(parts) > 2:
        # create level 1
        if parts[-1] in school_level:
            level1 = parts[-1]
        elif parts[-2] in school_level:
            level1 = parts[-2]

        # create level 2
        if parts[-1] in gender:
            level2 = parts[-1]

        # create level 0
        for var in school_level + gender:
            if var in name:
                name = name.replace('_' + var, '')

        return (name, level1, level2)


def get_education_data():
    PATH = DATA_PATH / 'world_bank' / 'API_4_DS2_en_csv_v2_3160069.csv'

    df = pd.read_csv(PATH, skiprows=4)
    indicators = get_education_indicators()

    df = df.rename(columns={
        'Country Code': 'country_code',
        'Country Name': 'country_name',
        'Indicator Code': 'indicator_code'
    })

    df = df.drop(columns=['Unnamed: 65', 'Indicator Name', 'country_name'])

    df = df.melt(id_vars=['country_code', 'indicator_code'], var_name='year')
    df.year = df.year.astype(int) # todo: to datetime

    df = df.join(indicators, on='indicator_code', how='right')
    df = df.drop(columns=['indicator_code'])
    df = df.pivot(index=['country_code', 'year'], columns='indicator', values='value')
    multi_columns = pd.MultiIndex.from_tuples([create_indicator_levels(name) for name in df.columns],
                                              names=['indicator', 'level', 'gender'])
    df.columns = multi_columns

    df = df.stack(level=[1, 2], dropna=False)

    df_meta = get_education_meta()

    df = df.join(df_meta, how='inner', on='country_code')

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
    df = df.groupby(['country_code', 'year', 'level']).mean()

    multi_columns = pd.MultiIndex.from_tuples([
        ('learning_outcome', 'total'),
        ('learning_outcome', 'male'),
        ('learning_outcome', 'female')],
        names=['indicator', 'gender'])
    df.columns = multi_columns

    df_total = df.groupby(['country_code', 'year']).mean()
    df_total = df_total.stack().reset_index().set_index(['country_code', 'year'])
    df_total['level'] = 'total'

    df = df.stack()
    df = df.reset_index().set_index(['country_code', 'year'])
    df.level = df.level.replace('pri', 'primary')
    df.level = df.level.replace('sec', 'secondary')

    df = pd.concat([df, df_total])
    df = df.reset_index().set_index(['country_code', 'year', 'level', 'gender'])

    return df


def get_gdp_data():
    PATH = DATA_PATH / 'maddison' / 'mpd2020.xlsx'

    df = pd.read_excel(PATH, sheet_name='Full data')
    df = df.drop(columns=['country'])
    df = df.rename(columns={'countrycode': 'country_code', 'pop': 'population'})
    df = df.set_index(['country_code', 'year'])

    return df


def merged_data(from_year=2000, europe=False, indexed=False):
    edu = get_education_data()
    hlo = get_hlo_data()

    df = edu.join(hlo)
    gdp = get_gdp_data()
    df = df.join(gdp, on=['country_code', 'year'])

    df = df.sort_index(axis=1, level='year')
    df = df.groupby(['country_code', 'level', 'gender']).ffill()

    df['education_spent'] = df.gdppc * df.education_expenditure_gdp_rate / 100

    df = df[df.index.isin([year for year in range(from_year, 2021)], level='year')]

    if europe:
        europe_countries = get_europe_countries()
        df = df[df.index.isin(europe_countries.country_code3, level='country_code')]

    df = df.reset_index()
    df.year = pd.to_datetime(df.year, format='%Y')

    if indexed:
        df = df.reset_index(['country_code', 'year', 'level', 'gender'])

    return df


if __name__ == '__main__':
    df = merged_data()
    df.to_csv(DATA_PATH / 'data.csv')
