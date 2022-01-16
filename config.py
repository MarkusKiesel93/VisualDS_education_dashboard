

class Config():
    def __init__(self, df):
        self.DATES = sorted(df.index.get_level_values('year').unique())
        self.GROUPS = {
            'region': sorted(df['region'].unique()),
            'income_group': sorted(df['income_group'].unique())
        }

    INDICATORS = {
        'learning_outcome': {
            'range': 'auto',
            'level_not_present': ['tertiary'],
            'gender_not_present': [],
        },
        'completion_rate': {
            'range': 'rate',
            'level_not_present': [],
            'gender_not_present': [],
        },
        'literacy_rate': {
            'range': 'rate',
            'level_not_present': ['primary', 'secondary', 'tertiary'],
            'gender_not_present': [],
        },
        'pupil_teacher_ratio': {
            'range': 'rate',
            'level_not_present': ['total'],
            'gender_not_present': ['female', 'male']
        }
    }

    BY = {
        'gdppc': {
            'range': 'auto',
            'scale': 'log',
            'level_not_present': [],
            'gender_not_present': [],
        },
        'population': {
            'range': 'auto',
            'scale': 'log',
            'level_not_present': [],
            'gender_not_present': [],
        },
        'education_spent': {
            'range': 'auto',
            'scale': 'log',
            'level_not_present': [],
            'gender_not_present': [],
        },
        'expenditure_per_student_rate': {
            'range': 'rate',
            'scale': 'linear',
            'level_not_present': ['total'],
            'gender_not_present': [],
        },
    }

    GROUP_BY = ['region', 'income_group']
    INFO_ITEMS = ['country_name', 'population', 'education_expenditure_gdp_rate', 'number_teachers']
    LEVELS = ['total', 'primary', 'secondary', 'tertiary']
    GENDER = ['total', 'female', 'male']
