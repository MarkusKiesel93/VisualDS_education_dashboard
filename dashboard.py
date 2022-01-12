from bokeh.transform import factor_cmap, factor_mark
from bokeh.models import CategoricalColorMapper, Legend, LinearColorMapper
from bokeh.palettes import Category10, Greens9
from bokeh.layouts import column, row, layout
from bokeh.models import ColumnDataSource, GeoJSONDataSource, Slider, Button, Patches, Select, Range1d, CategoricalColorMapper, ColorBar
from bokeh.plotting import figure, curdoc
from bokeh.io import show, output_notebook

from data import get_merged_data, get_geo_data

df = get_merged_data(year_as_datetime=False)

# todo: compute everything beforehand and use from dicts instead
LOOOKUP = {
    'indicator': {
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
    },
    'by': {
        'gdppc': {
            'range': 'auto',
            'level_not_present': [],
            'gender_not_present': [],
        },
        'population': {
            'range': 'auto',
            'level_not_present': [],
            'gender_not_present': [],
        },
        'education_spent': {
            'range': 'auto',
            'level_not_present': [],
            'gender_not_present': [],
        },
        'pupil_teacher_ratio': {
            'range': 'rate',
            'level_not_present': [],
            'gender_not_present': [],
        },
        'expenditure_per_student_rate': {
            'range': 'rate',
            'level_not_present': [],
            'gender_not_present': [],
        },
    }
}


# define helper functions:
def select_range(type, value, level, gender):
    range_type = LOOOKUP[type][value]['range']
    if range_type == 'auto':
        if type == 'indicator':
            inicator = select_indicator.value
        else:
            inicator = select_by.value
        min = df[(inicator, level, gender)].min() * 0.9
        max = df[(inicator, level, gender)].max() * 1.1
    else:
        min, max = 0, 105

    return min, max


def format_label(indicator, x_label=False):
    words = indicator.split('_')
    formatted = ' '.join([word.capitalize() for word in words])
    if x_label:
        if use_scale(indicator) == 'log':
            formatted = 'log ' + formatted
    return formatted


def create_slider_widget(title, options):
    return Slider(
        title=title,
        value=options[-1],
        start=options[0],
        end=options[-1],
        step=1
    )


def create_select_widget(title, options):
    value = options[0]
    options = [(option, format_label(option)) for option in options]
    return Select(
        title=title,
        value=value,
        options=options
    )


def create_options(type, options):
    restricted_options = options.copy()
    for value in LOOOKUP['indicator'][select_indicator.value][f'{type}_not_present']:
        restricted_options.remove(value)
    for value in LOOOKUP['by'][select_by.value][f'{type}_not_present']:
        restricted_options.remove(value)
    return restricted_options


def update_view(attr, old, new):
    dashboard.children[0].children[1] = scatter()
    dashboard.children[1] = choropleth()


def update_data(attr, old, new):
    source.data = df.xs(slider_year.value, level='year').xs((select_level.value, select_gender.value), axis=1, level=('level', 'gender'))


def update_view_tools(attr, old, new):
    level_options = create_options('level', LEVELS)
    select_level.options = level_options
    select_level.value = level_options[0]
    gender_options = create_options('gender', GENDER)
    select_gender.options = gender_options
    select_gender.value = level_options[0]
    update_view(attr, old, new)

def use_scale(x_value):
    if x_value.split('_')[-1] in ['rate', 'ratio']:
        return 'linear'
    else:
        return 'log'


def create_tooltips(values):
    # todo: maybe use info items here as well
    tooltips = [(format_label(value), f'@{value}') for value in values]
    tooltips.insert(0, ('Country', '@country_name'))
    return tooltips


# todo: do something with this values:
OTHER_INDICATORS = [
    'compulsory_education_duration',  # separate plot maby compare counties
    'education_pupils_rate'   # separate plot for one country info betwee female male for secondary and primary
    'expenditure_rate',  # separate plot for one country info between primary, secondary, and tertiary
    'number_teachers_rate',  # separate plot for one country info betwee female male for secondary and primary
]

DATES = sorted(df.index.get_level_values('year').unique())
GROUPS = {
    'region': sorted(df[('region', 'total', 'total')].unique()),
    'income_group': sorted(df[('income_group', 'total', 'total')].unique())
}
INDICATORS = ['learning_outcome', 'completion_rate', 'literacy_rate', 'pupil_teacher_ratio']
BY = ['gdppc', 'population', 'education_spent', 'pupil_teacher_ratio', 'expenditure_per_student_rate']
COLOR_BY = ['region', 'income_group']
INFO_ITEMS = ['country_name', 'population', 'education_expenditure_gdp_rate', 'number_teachers']
LEVELS = ['total', 'primary', 'secondary', 'tertiary']
GENDER = ['total', 'female', 'male']


source = ColumnDataSource(df.xs(DATES[-1], level='year').xs(('total', 'total'), axis=1, level=('level', 'gender')))

color_mapper = LinearColorMapper(palette=Category10[7])

# define widgets
slider_year = create_slider_widget('Year', DATES)
select_indicator = create_select_widget('Indicator:', INDICATORS)
select_by = create_select_widget('By:', BY)
select_color = create_select_widget('Color by:', COLOR_BY)
select_level = create_select_widget('Education Level:', create_options('level', LEVELS))
select_gender = create_select_widget('Gender:', create_options('gender', GENDER))

# add callbacks to widgets
slider_year.on_change('value', update_data)
select_indicator.on_change('value', update_view_tools)  # todo: reset level and gender
select_by.on_change('value', update_view_tools)  # todo: reset level and gender
select_color.on_change('value', update_view)
select_level.on_change('value', update_data)
select_gender.on_change('value', update_data)


# scatterplot function
def scatter():
    fig = figure(
        height=400,
        width=800,
        tools='hover,tap,pan,box_zoom,wheel_zoom,zoom_in,zoom_out,lasso_select,save,reset',
        toolbar_location='above',
        x_axis_type=use_scale(select_by.value),
        y_range=select_range('indicator', select_indicator.value, select_level.value, select_gender.value),
        x_range=select_range('by', select_by.value, select_level.value, select_gender.value))
    fig.yaxis.axis_label = format_label(select_indicator.value)
    fig.xaxis.axis_label = format_label(select_by.value, x_label=True)
    fig.add_layout(Legend(), 'right')
    fig.legend.location = 'top_left'
    fig.legend.title = format_label(select_color.value)

    # set tooltips
    fig.hover.tooltips = create_tooltips([select_indicator.value, select_by.value])

    # create scatterplot
    fig.scatter(
        x=select_by.value,
        y=select_indicator.value,
        source=source,
        color=factor_cmap(
            field_name=select_color.value,
            palette=Category10[len(GROUPS[select_color.value])],
            factors=GROUPS[select_color.value]),
        size=9,
        hover_line_color='black',
        legend_group=select_color.value,
        fill_alpha=0.5)

    return fig


# chropleth function
def choropleth():
    geo_data = get_geo_data()
    df = get_merged_data(from_year=2020, year_as_datetime=False)
    df = df.xs(2020, level='year').xs(('total', 'total'), axis=1, level=('level', 'gender'))
    geo_data = geo_data.join(df, on='country_code')
    geo_source = GeoJSONDataSource(geojson=geo_data.to_json())

    fig = figure(
        plot_height=500,
        plot_width=900,
        tools='hover,tap,wheel_zoom,zoom_in,zoom_out,save,reset',
        x_axis_location=None,
        y_axis_location=None)
    fig.grid.visible = False

    color_mapper = LinearColorMapper(
        palette=list(reversed(Greens9)),
        low=0,
        high=100)

    # patches = Patches(
    #     xs="xs", ys="ys",
    #     fill_alpha=0.7, 
    #     fill_color={'field': 'literacy_rate', 'transform': color_mapper},
    #     line_color='white', 
    #     line_width=0.3)
    # fig.add_glyph(geo_source, patches)

    fig.patches(
        xs="xs",
        ys="ys",
        source=geo_source,
        fill_alpha=0.7,
        fill_color={'field': select_indicator.value, 'transform': color_mapper},
        line_color='white',
        line_width=0.3,
        hover_line_color='black',
    )

    # set tooltips
    fig.hover.tooltips = create_tooltips([select_indicator.value, select_by.value])

    color_bar = ColorBar(
        color_mapper=color_mapper,
        location="bottom_left", orientation="horizontal",
        title=format_label(select_indicator.value),
        title_text_font_size="14px", title_text_font_style="bold",
        background_fill_alpha=0.0)
    fig.add_layout(color_bar)

    return fig


## add tools and different plots to oune dashboard
tools = column(slider_year, select_indicator, select_by, select_level, select_gender, select_color)
dashboard = layout(
    row(tools, scatter()),
    row(choropleth())
)

curdoc().add_root(dashboard)
curdoc().title = 'World Education Dashboard'
