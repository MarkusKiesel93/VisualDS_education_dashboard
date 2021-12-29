from bokeh.transform import factor_cmap, factor_mark
from bokeh.models import CategoricalColorMapper, Legend, LinearColorMapper
from bokeh.palettes import Category10
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, GeoJSONDataSource, Slider, Button, Patches, Select, Range1d, CategoricalColorMapper
from bokeh.plotting import figure
from bokeh.io import show, output_notebook, curdoc

from data import get_merged_data

df = get_merged_data(year_as_datetime=False)
df.head()


def select_range(indicator, level='total', gender='total', log=False):
    min = df[(indicator, level, gender)].min() * 0.9
    max = df[(indicator, level, gender)].max() * 1.1

    return min, max


DATES = sorted(df.index.get_level_values('year').unique())
GROUPS = {
    'region': sorted(df[('region', 'total', 'total')].unique()),
    'income_group': sorted(df[('income_group', 'total', 'total')].unique())
}

source = ColumnDataSource(df.xs(DATES[-1], level='year').xs(('total', 'total'), axis=1, level=('level', 'gender')))

color_mapper = LinearColorMapper(palette=Category10[7])


def update_year(attr, old, new):
    source.data = df.xs(new, level='year').xs(('total', 'total'), axis=1, level=('level', 'gender'))


def update_color(attr, old, new):
    layout.children[1] = scatter()


# year slider
slider_year = Slider(
    title='Year',
    value=DATES[-1],
    start=DATES[0],
    end=DATES[-1],
    step=1)
slider_year.on_change('value', update_year)


# color selecter
select_color = Select(
    title='Color by:',
    value='region',
    options=[('region', 'Region'), ('income_group', 'Income Group')])
select_color.on_change('value', update_color)


def scatter():
    p = figure(
        height=400,
        width=800,
        title='Harmonized Learning outcome by GDPPC',
        x_axis_type='log',
        y_range=select_range('learning_outcome'),
        x_range=select_range('gdppc'))
    p.xaxis.axis_label = 'log GDP per capita'
    p.yaxis.axis_label = 'Harmonized Learning Outcome'
    p.add_layout(Legend(), 'right')
    p.legend.location = 'top_left'
    p.legend.title = 'Regions'

    p.scatter(
        'gdppc',
        'learning_outcome',
        source=source,
        color=factor_cmap(
            field_name=select_color.value,
            palette=Category10[len(GROUPS[select_color.value])],
            factors=GROUPS[select_color.value]),
        size=9,
        legend_group=select_color.value,
        fill_alpha=0.5)

    return p


tools = column(slider_year, select_color)
top_right = column(scatter())
layout = row(tools, top_right)

curdoc().add_root(layout)
curdoc().title = 'Dashboard'
