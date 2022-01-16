class Config():
    def __init__(self, df):
        self.DATES = sorted(df.index.get_level_values('year').unique())
        self.GROUPS = {
            'region': sorted(df['region'].unique()),
            'income_group': sorted(df['income_group'].unique())
        }
        self.COL1_WIDTH = self.get_size(self.WIDTH, 2, 3)
        self.COL2_WIDTH = self.get_size(self.WIDTH, 1, 3)
        self.COL1_HEIGHT = self.get_size(self.HEIGHT, 1, 2)
        self.COL2_HEIGHT = self.get_size(self.HEIGHT, 1, 3)
        self.TOOL_WIDTH = self.get_size(self.COL1_WIDTH, 2, 7)

    def get_size(self, size, numerator, denominator):
        return int(size * numerator / denominator)

    HEIGHT = 1000
    WIDTH = 1800

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
        'primary': '#1f77b4',
        'secondary': '#9467bd',
        'tertiary': '#d62728'
    }
