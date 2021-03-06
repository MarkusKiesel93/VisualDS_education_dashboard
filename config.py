class Config():
    def __init__(self, df):
        self.DATES = sorted(df.index.get_level_values('year').unique())
        self.GROUPS = {
            'region': sorted(df['region'].unique()),
            'income_group': sorted(df['income_group'].unique())
        }
        self.COL1_WIDTH = int(self.WIDTH * 3 / 5)
        self.COL2_WIDTH = self.WIDTH - self.COL1_WIDTH
        self.COL1_HEIGHT = int(self.HEIGHT * 1 / 2)
        self.COL2_HEIGHT1 = int(self.HEIGHT * 4 / 10)
        self.COL2_HEIGHT2 = int(self.HEIGHT * 3 / 10)
        self.TOOL_WIDTH = int(self.COL1_WIDTH * 2 / 7)

    HEIGHT = 1000
    WIDTH = 2000

    INDICATORS = {
        'learning_outcome': {
            'range': 'auto',
            'level_not_present': ['tertiary'],
            'gender_not_present': [],
        },
        'completion_rate': {
            'range': 'rate',
            'level_not_present': ['total'],
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

    GROUP_BY = ['income_group', 'region']
    INFO_ITEMS = ['country_name', 'population', 'education_expenditure_gdp_rate', 'number_teachers']
    LEVELS = ['total', 'primary', 'secondary', 'tertiary']
    GENDER = ['total', 'female', 'male']

    GENDER_COLORS = {
        'female': '#e377c2',
        'total': '#ff7f0e',
        'male': '#1f77b4'
    }
    LEVEL_COLORS = {
        'total': '#ff7f0e',
        'primary': '#2ca02c',
        'secondary': '#9467bd',
        'tertiary': '#8c564b'
    }
