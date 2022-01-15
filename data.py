from lib2to3.pgen2.pgen import DFAState
from locale import D_FMT
import pandas as pd
import geopandas as gpd
from pathlib import Path

DATA_PATH = Path(__file__).parent / 'data'


def get_geo_data():
    PATH = DATA_PATH / 'ne_110m_admin_0_countries' / 'ne_110m_admin_0_countries.shp'

    df = gpd.read_file(PATH)
    df = df[['SOV_A3', 'geometry']]
    df = df.rename(columns={'SOV_A3': 'country_code'})
    df = df.set_index('country_code')
    df = df.drop(index=['ATA'])  # remove antarctis

    return df


def get_education_indicators(without_info=True):
    PATH = DATA_PATH / 'world_bank' / 'selected_indicators.csv'

    df = pd.read_csv(PATH)
    df = df.set_index('indicator_code')
    if without_info:
        df = df.indicator

    return df


def get_education_meta(multi_index):
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

    if multi_index:
        df.columns = create_multi_index(df.columns)

        levels = ['primary', 'secondary', 'tertiary', 'total']
        genders = ['male', 'female', 'total']
        for level in levels:
            for gender in genders:
                df[('region', level, gender)] = df[('region', 'total', 'total')]
                df[('income_group', level, gender)] = df[('income_group', 'total', 'total')]
                df[('country_name', level, gender)] = df[('country_name', 'total', 'total')]

    return df


def create_multi_index(columns):
    level_names = []
    for name in columns:
        parts = name.split('_')

        levels = ['primary', 'secondary', 'tertiary', 'total']
        genders = ['female', 'male', 'total']
        level1 = 'total'
        level2 = 'total'

        if len(parts) > 2:
            # create level 2
            if parts[-1] in genders:
                level2 = parts[-1]
                name = name.replace('_' + level2, '')

            # create level 1
            if parts[-2] in levels:
                level1 = parts[-2]
                name = name.replace('_' + level1, '')
        level_names.append((name, level1, level2))

    return pd.MultiIndex.from_tuples(level_names, names=['indicator', 'level', 'gender'])


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
    df.year = df.year.astype(int)

    df = df.join(indicators, on='indicator_code', how='right')
    df = df.drop(columns=['indicator_code'])
    df = df.pivot(index=['country_code', 'year'], columns='indicator', values='value')

    levels = ['primary', 'secondary', 'tertiary', 'total']
    genders = ['male', 'female', 'total']
    for gender in genders:
        cols = [f'completion_rate_{level}_{gender}' for level in levels[:-1]]
        df[f'completion_rate_total_{gender}'] = df[cols].mean(axis=1)
    for gender in genders[:-1]:
        df[f'compulsory_education_duration_total_{gender}'] = df['compulsory_education_duration_total_total']
    for level in levels:
        for gender in genders:
            df[f'education_expenditure_gdp_rate_{level}_{gender}'] = df['education_expenditure_gdp_rate_total_total']

    for level in levels[0:2]:
        df[f'education_pupils_rate_{level}_total'] = 100
        df[f'education_pupils_rate_{level}_male'] = 100 - df[f'education_pupils_rate_{level}_female']
        for gender in genders[:-1]:
            df[f'education_pupils_{level}_{gender}'] = df[f'education_pupils_{level}_total'] * df[f'education_pupils_rate_{level}_{gender}'] / 100

    for level in levels[:-1]:
        for gender in genders[:-1]:
            df[f'expenditure_per_student_rate_{level}_{gender}'] = df[f'expenditure_per_student_rate_{level}_total']
            df[f'expenditure_rate_{level}_{gender}'] = df[f'expenditure_rate_{level}_total']

    df.columns = create_multi_index(df.columns)

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

    df = df.unstack(level=['level', 'gender'])

    return df


def get_gdp_data():
    PATH = DATA_PATH / 'maddison' / 'mpd2020.xlsx'

    df = pd.read_excel(PATH, sheet_name='Full data')
    df = df.drop(columns=['country'])
    df = df.rename(columns={'countrycode': 'country_code', 'pop': 'population'})
    df = df.set_index(['country_code', 'year'])

    df.columns = create_multi_index(df.columns)

    levels = ['primary', 'secondary', 'tertiary', 'total']
    genders = ['male', 'female', 'total']
    for level in levels:
        for gender in genders:
            df[('gdppc', level, gender)] = df[('gdppc', 'total', 'total')]
            df[('population', level, gender)] = df[('population', 'total', 'total')]

    return df


def get_merged_data(from_year=2000, ffill=True, indexed=True, year_as_datetime=True, multi_index=False):
    df = get_education_data()
    edu_meta = get_education_meta(multi_index)
    hlo = get_hlo_data()
    gdp = get_gdp_data()

    df = df.join(hlo)
    df = df.join(gdp, on=['country_code', 'year'])

    df[('education_spent', 'total', 'total')] = df[('gdppc', 'total', 'total')] * df[('education_expenditure_gdp_rate', 'total', 'total')] /  100
    levels = ['primary', 'secondary', 'tertiary', 'total']
    genders = ['male', 'female', 'total']
    for level in levels:
        for gender in genders:
            df[('education_spent', level, gender)] = df[('education_spent', 'total', 'total')]

    if ffill:
        df = df.sort_index(level='year')
        df = df.groupby(['country_code']).ffill()

    df = df[df.index.isin([year for year in range(from_year, 2021)], level='year')]
    if year_as_datetime:
        df.index = df.index.set_levels([df.index.levels[0], pd.to_datetime(df.index.levels[1], format='%Y')])

    if not multi_index:
        df.columns = ['_'.join(list(levels)) for levels in df.columns]

    df = df.join(edu_meta, how='inner', on='country_code')

    return df


if __name__ == '__main__':
    df = get_merged_data(year_as_datetime=False)
    df.to_csv(DATA_PATH / 'data.csv')

    df_2020_total = df.xs(2020, level='year').xs(('total', 'total'), axis=1, level=('level', 'gender'))
    df_2020_total.to_csv(DATA_PATH / 'data_2020_total.csv')

    df_total = df.xs(('total', 'total'), axis=1, level=('level', 'gender'))
    df_total.to_csv(DATA_PATH / 'data_total.csv')
