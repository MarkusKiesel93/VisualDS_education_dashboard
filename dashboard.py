from bokeh.transform import factor_cmap, factor_mark
from bokeh.models import CategoricalColorMapper, Legend, LinearColorMapper
from bokeh.palettes import Category10, Greens9
from bokeh.layouts import column, row, layout
from bokeh.models import ColumnDataSource, GeoJSONDataSource, Slider, Button, Patches, Select, Range1d, CategoricalColorMapper, ColorBar
from bokeh.plotting import figure, curdoc
from bokeh.io import show, output_notebook

from data import get_merged_data, get_geo_data

df = get_merged_data(year_as_datetime=False)


# Define helper functions:


def select_range(indicator, level='total', gender='total'):
    min = df[(indicator, level, gender)].min() * 0.9
    max = df[(indicator, level, gender)].max() * 1.1

    return min, max


def format_indicator(indicator):
    words = indicator.split('_')
    return ' '.join([word.capitalize() for word in words])


def create_options(indicators):
    return [(indicator, format_indicator(indicator)) for indicator in indicators]


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
INDICATORS = ['learning_outcome', 'completion_rate', 'literacy_rate', 'school_enrollment', 'pupil_teacher_ratio']
BY = ['gdppc', 'population', 'education_spent', 'pupil_teacher_ratio', 'expenditure_per_student_rate']
COLOR_BY = ['region', 'income_group']
INFO_ITEMS = ['country_name', 'population', 'education_expenditure_gdp_rate', 'number_teachers']
LEVELS = ['total', 'primary', 'secondary', 'tertiary']
GENDER = ['total', 'female', 'male']

source = ColumnDataSource(df.xs(DATES[-1], level='year').xs(('total', 'total'), axis=1, level=('level', 'gender')))

color_mapper = LinearColorMapper(palette=Category10[7])


def update_view(attr, old, new):
    plots.children[0].children[1] = scatter()
    # todo: add choropleth


def update_data(attr, old, new):
    print(select_level.value)
    print(select_gender.value)#
    print(df.xs(slider_year.value, level='year').xs((select_level.value, select_gender.value), axis=1, level=('level', 'gender')))
    source.data = df.xs(slider_year.value, level='year').xs((select_level.value, select_gender.value), axis=1, level=('level', 'gender'))


# Define Widgets:

# year slider
slider_year = Slider(
    title='Year',
    value=DATES[-1],
    start=DATES[0],
    end=DATES[-1],
    step=1)
slider_year.on_change('value', update_data)


# color selecter
select_color = Select(
    title='Color by:',
    value='region',
    options=[('region', 'Region'), ('income_group', 'Income Group')])
select_color.on_change('value', update_view)

select_indicator = Select(
    title='Indicator',
    value='learning_outcome',
    options=create_options(INDICATORS)
)
select_indicator.on_change('value', update_view)

select_by = Select(
    title='By',
    value='gdppc',
    options=create_options(BY)
)
select_by.on_change('value', update_view)


# level selecter
select_level = Select(
    title='Education Level',
    value='total',
    options=create_options(LEVELS)
)
select_level.on_change('value', update_data)


# gender selecter
select_gender = Select(
    title='Gender',
    value='total',
    options=create_options(GENDER)
)
select_gender.on_change('value', update_data)


def scatter():
    fig = figure(
        height=400,
        width=800,
        tools='hover,tap,pan,box_zoom,wheel_zoom,zoom_in,zoom_out,lasso_select,save,reset',
        toolbar_location='above',
        x_axis_type='log',
        y_range=select_range(select_indicator.value),
        x_range=select_range(select_by.value))
    fig.xaxis.axis_label = 'log GDP per capita'
    fig.yaxis.axis_label = 'Harmonized Learning Outcome'
    fig.add_layout(Legend(), 'right')
    fig.legend.location = 'top_left'
    fig.legend.title = 'Regions'

    # set tooltips
    fig.hover.tooltips = [
        ('Country', '@country_name'),
        ('Region', '@region'),
        ('Income Group', '@income_group'),
        ('Bla Bla', f'@{select_indicator.value}'),
        ('Bla Bla', f'@{select_by.value}')
    ]

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
    fig.title.text = 'Literacy Rate by Country 2020'
    fig.title.align = 'center'
    fig.title.text_font_size = '20px'

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
        fill_color={'field': 'literacy_rate', 'transform': color_mapper},
        line_color='white',
        line_width=0.3,
        hover_line_color='black',
    )

    # set tooltips
    fig.hover.tooltips = [
        ('Country', '@country_name'),
        ('Region', '@region'),
        ('Income Group', '@income_group'),
        ('Bla Bla', f'@{select_indicator.value}'),
        ('Bla Bla', f'@{select_by.value}')
    ]

    color_bar = ColorBar(
        color_mapper=color_mapper,
        location="bottom_left", orientation="horizontal",
        title="Literacy Rate",
        title_text_font_size="14px", title_text_font_style="bold",
        background_fill_alpha=0.0)
    fig.add_layout(color_bar)

    return fig


tools = column(slider_year, select_indicator, select_by, select_level, select_gender, select_color)

plots = layout(
    row(tools, scatter()),
    row(choropleth())
)

curdoc().add_root(plots)
curdoc().title = 'World Education Dashboard'
