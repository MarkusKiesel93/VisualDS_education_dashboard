from bokeh.transform import factor_cmap
from bokeh.models import Legend, LinearColorMapper, CategoricalColorMapper
from bokeh.palettes import Category10, Category20, Blues9
from bokeh.layouts import column, row, layout
from bokeh.models import ColumnDataSource, GeoJSONDataSource, Slider, Select, ColorBar, CheckboxGroup
from bokeh.plotting import figure, curdoc
from bokeh.transform import dodge
import pandas as pd
from data import get_merged_data, get_geo_data
from config import Config

# load datasets
df = get_merged_data()
df_geo = get_geo_data()

settings = Config(df)


# define helper functions:
def color_by_group(group):
    color_mapper = CategoricalColorMapper(
        palette=Category10[len(settings.GROUPS[select_group.value])],
        factors=settings.GROUPS[select_group.value]
    )
    return color_mapper.palette[color_mapper.factors.index(group)]


def color_sequential(n, i):
    if n < 10:
        colors = Category10[10]
        return colors[i % 10]
    else:
        colors = Category20[20]
        return colors[i % 20]


def indicator_col(indicator=None, level=None, gender=None):
    if not indicator:
        indicator = select_indicator.value
    if not level:
        level = select_level.value
    if not gender:
        gender = select_gender.value
    return '_'.join([indicator, level, gender])


def select_range(config, indicator, level=None, gender=None):
    if config[indicator]['range'] == 'rate':
        min, max = 0, 105
    else:
        min = df[indicator_col(indicator, level, gender)].min() * 0.9
        max = df[indicator_col(indicator, level, gender)].max() * 1.1

    return min, max


def format_label(indicator, x_label=False):
    words = indicator.split('_')
    formatted = ' '.join([word.capitalize() for word in words])
    if x_label:
        if 0 in checkbox_group.active:
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
    return Select(
        title=title,
        value=value,
        options=format_options(options)
    )


def create_checkbox_widget(labels, active):
    return CheckboxGroup(
        labels=labels,
        active=active
    )


def create_options(type, options):
    restricted_options = options.copy()
    for value in settings.INDICATORS[select_indicator.value][f'{type}_not_present']:
        if value in restricted_options:
            restricted_options.remove(value)
    for value in settings.BY[select_by.value][f'{type}_not_present']:
        if value in restricted_options:
            restricted_options.remove(value)
    return restricted_options


def format_options(options):
    return [(option, format_label(option)) for option in options]


def geo_index(selected_countries):
    index = []
    geo_country_codes = list(subset_geo.reset_index()['country_code'].values)
    for country in selected_countries:
        if country in geo_country_codes:
            index.append(geo_country_codes.index(country))
    return index


def update_view(attr, old, new):
    dashboard.children[0].children[0].children[0].children[1] = choropleth()
    dashboard.children[0].children[0].children[1] = scatter()
    dashboard.children[0].children[1].children[0] = line_chart()
    dashboard.children[0].children[1].children[1] = bar_chart_gender()
    dashboard.children[0].children[1].children[2] = bar_chart_level()


def update_by_select(attr, old, new):
    data = source.to_df().iloc[new]
    selected_countries = data['country_code'].values
    dashboard.children[0].children[1].children[0] = line_chart(selected_countries)
    dashboard.children[0].children[1].children[1] = bar_chart_gender(data)
    dashboard.children[0].children[1].children[2] = bar_chart_level(data)
    geo_source.selected.indices = geo_index(selected_countries)


def update_data(attr, old, new):
    subset = df.xs(slider_year.value, level='year')
    subset_geo = df_geo.join(subset, on='country_code')
    source.data = subset
    geo_source.geojson = subset_geo.to_json()
    update_view(attr, old, new)


def update_view_tools(attr, old, new):
    if settings.BY[select_by.value]['scale'] == 'log':
        if 0 not in checkbox_group.active:
            checkbox_group.active.append(0)
    else:
        checkbox_group.active.remove(0)
    level_options = create_options('level', settings.LEVELS)
    select_level.options = format_options(level_options)
    select_level.value = level_options[0]
    gender_options = create_options('gender', settings.GENDER)
    select_gender.options = format_options(gender_options)
    select_gender.value = gender_options[0]
    update_view(attr, old, new)


def create_tooltips(values):
    tooltips = [(format_label(value), '@' + indicator_col(value)) for value in values]
    tooltips.insert(0, ('Country', '@country_name'))
    return tooltips


subset = df.xs(settings.DATES[-1], level='year')
subset_geo = df_geo.join(subset, on='country_code')
source = ColumnDataSource(subset)
geo_source = GeoJSONDataSource(geojson=subset_geo.to_json())

# define widgets
slider_year = create_slider_widget('Year', settings.DATES)
select_indicator = create_select_widget('Indicator:', list(settings.INDICATORS.keys()))
select_by = create_select_widget('By:', list(settings.BY.keys()))
select_group = create_select_widget('Group by:', settings.GROUP_BY)
select_level = create_select_widget('Education Level:', create_options('level', settings.LEVELS))
select_gender = create_select_widget('Gender:', create_options('gender', settings.GENDER))
checkbox_group = create_checkbox_widget(['Log scale'], [0])

# add callbacks to widgets
slider_year.on_change('value', update_data)
select_indicator.on_change('value', update_view_tools)
select_by.on_change('value', update_view_tools)
select_group.on_change('value', update_view)
select_level.on_change('value', update_data)
select_gender.on_change('value', update_data)
checkbox_group.on_change('active', update_view)
source.selected.on_change('indices', update_by_select)


# scatterplot function
def scatter():
    fig = figure(
        height=settings.COL1_HEIGHT,
        width=settings.COL1_WIDTH,
        tools='hover,tap,pan,box_zoom,wheel_zoom,zoom_in,zoom_out,lasso_select,save,reset',
        toolbar_location='above',
        x_axis_type='log' if 0 in checkbox_group.active else 'linear',
        y_range=select_range(settings.INDICATORS, select_indicator.value),
        x_range=select_range(settings.BY, select_by.value))
    fig.yaxis.axis_label = format_label(select_indicator.value)
    fig.xaxis.axis_label = format_label(select_by.value, x_label=True)
    fig.add_layout(Legend(), 'right')
    fig.legend.title = format_label(select_group.value)
    fig.title.text = 'Data Explorer'
    fig.title.align = 'center'
    fig.title.text_font_size = '20px'

    # set tooltips
    fig.hover.tooltips = create_tooltips([select_indicator.value, select_by.value])

    # create scatterplot
    fig.scatter(
        x=indicator_col(select_by.value),
        y=indicator_col(select_indicator.value),
        source=source,
        color=factor_cmap(
            field_name=select_group.value,
            palette=Category10[len(settings.GROUPS[select_group.value])],
            factors=settings.GROUPS[select_group.value]),
        size=9,
        hover_line_color='black',
        legend_group=select_group.value,
        fill_alpha=0.5)

    return fig


# chropleth function
def choropleth():
    fig = figure(
        height=settings.COL1_HEIGHT,
        width=settings.COL1_WIDTH - settings.TOOL_WIDTH,
        tools='hover,tap,wheel_zoom,box_zoom,zoom_in,zoom_out,save,reset',
        toolbar_location='above',
        x_axis_location=None,
        y_axis_location=None)
    fig.grid.visible = False
    fig.title.text = 'Difference by Country'
    fig.title.align = 'center'
    fig.title.text_font_size = '20px'

    low, high = select_range(settings.INDICATORS, select_indicator.value)
    color_mapper = LinearColorMapper(
        palette=list(reversed(Blues9)),
        low=low,
        high=high)

    fig.patches(
        xs='xs',
        ys='ys',
        source=geo_source,
        fill_alpha=0.9,
        fill_color={'field': indicator_col(select_indicator.value), 'transform': color_mapper},
        line_color='white',
        line_width=0.3,
        hover_line_color='black',
    )

    # set tooltips
    fig.hover.tooltips = create_tooltips([select_indicator.value, select_by.value])

    color_bar = ColorBar(
        color_mapper=color_mapper,
        location='bottom_left', orientation='horizontal',
        title=format_label(select_indicator.value),
        title_text_font_size='14px', title_text_font_style='bold',
        scale_alpha=0.9,
        background_fill_alpha=0.0)
    fig.add_layout(color_bar)

    return fig


def line_chart(countries=[]):
    fig = figure(
        height=settings.COL2_HEIGHT1,
        width=settings.COL2_WIDTH,
        x_range=(settings.DATES[0], settings.DATES[-1]),
        y_range=select_range(settings.INDICATORS, select_indicator.value)
    )
    fig.xaxis.axis_label = 'Year'
    fig.yaxis.axis_label = format_label(select_indicator.value)
    fig.add_layout(Legend(), 'right')
    fig.legend.title = format_label(select_group.value)
    fig.title.text = 'Development over Years'
    fig.title.align = 'center'
    fig.title.text_font_size = '20px'

    if len(countries) < 1:
        data = df.groupby([select_group.value, 'year']).mean().reset_index()
        for group in settings.GROUPS[select_group.value]:
            fig.line(
                'year',
                indicator_col(),
                source=ColumnDataSource(data[data[select_group.value] == group]),
                color=color_by_group(group),
                legend_group=select_group.value,
            )

    else:
        n = len(countries)
        for i, country in enumerate(countries):
            fig.line(
                'year',
                indicator_col(),
                source=ColumnDataSource(df.xs(country, level='country_code')),
                color=color_sequential(n, i),
                legend_group='country_name',
            )
        fig.legend.title = format_label('country_name')

    return fig


def bar_chart_gender(data=pd.DataFrame()):
    dodge_values = [0.0, -0.15, 0.15]

    if data.shape[0] < 1:
        source = ColumnDataSource(df.xs(slider_year.value, level='year')
                                  .groupby([select_group.value]).mean().reset_index())

        fig = figure(
            height=settings.COL2_HEIGHT2,
            width=settings.COL2_WIDTH,
            x_range=source.data[select_group.value],
            y_range=(0, select_range(settings.INDICATORS, select_indicator.value)[1]),
            toolbar_location=None,
            tools=''
        )

        for i, (gender, label) in enumerate(select_gender.options):
            fig.vbar(
                x=dodge(select_group.value, dodge_values[i], range=fig.x_range),
                top=indicator_col(gender=gender),
                source=source,
                width=0.15,
                color=settings.GENDER_COLORS[gender],
                alpha=0.7,
                legend_label=label
            )

    else:
        fig = figure(
            height=settings.COL2_HEIGHT2,
            width=settings.COL2_WIDTH,
            x_range=data['country_name'],
            y_range=(0, select_range(settings.INDICATORS, select_indicator.value)[1]),
            toolbar_location=None,
            tools=''
        )

        source = ColumnDataSource(data=data)
        for i, (gender, label) in enumerate(select_gender.options):
            fig.vbar(
                x=dodge('country_name', dodge_values[i], range=fig.x_range),
                top=indicator_col(gender=gender),
                source=source,
                width=0.15,
                color=settings.GENDER_COLORS[gender],
                alpha=0.7,
                legend_label=label
            )
    fig.add_layout(Legend(items=fig.legend.items), 'right')
    fig.legend[1].visible = False
    fig.xaxis.major_label_orientation = 120
    fig.yaxis.axis_label = format_label(select_indicator.value)
    fig.title.text = 'Difference by Gender'
    fig.title.align = 'center'
    fig.title.text_font_size = '20px'

    return fig


def bar_chart_level(data=pd.DataFrame()):
    dodge_values = [-0.225, -0.075, 0.075, 0.225]

    if data.shape[0] < 1:
        source = ColumnDataSource(df.xs(slider_year.value, level='year')
                                  .groupby([select_group.value]).mean().reset_index())

        fig = figure(
            height=settings.COL2_HEIGHT2,
            width=settings.COL2_WIDTH,
            x_range=source.data[select_group.value],
            y_range=(0, select_range(settings.INDICATORS, select_indicator.value)[1]),
            toolbar_location=None,
            tools=''
        )

        for i, (level, label) in enumerate(select_level.options):
            fig.vbar(
                x=dodge(select_group.value, dodge_values[i], range=fig.x_range),
                top=indicator_col(level=level),
                source=source,
                width=0.15,
                color=settings.LEVEL_COLORS[level],
                alpha=0.7,
                legend_label=label
            )
    else:
        fig = figure(
            height=settings.COL2_HEIGHT2,
            width=settings.COL2_WIDTH,
            x_range=data['country_name'],
            y_range=(0, select_range(settings.INDICATORS, select_indicator.value)[1]),
            toolbar_location=None,
            tools=''
        )

        source = ColumnDataSource(data=data)

        for i, (level, label) in enumerate(select_level.options):
            fig.vbar(
                x=dodge('country_name', dodge_values[i], range=fig.x_range),
                top=indicator_col(level=level),
                source=source,
                width=0.15,
                color=settings.LEVEL_COLORS[level],
                alpha=0.7,
                legend_label=label
            )
    fig.add_layout(Legend(items=fig.legend.items), 'right')
    fig.legend[1].visible = False
    fig.xaxis.major_label_orientation = 120
    fig.yaxis.axis_label = format_label(select_indicator.value)
    fig.title.text = 'Difference by Education Level'
    fig.title.align = 'center'
    fig.title.text_font_size = '20px'

    return fig


# add tools and different plots to oune dashboard
tools = column(slider_year, select_indicator, select_by, select_level, select_gender, select_group, checkbox_group)
dashboard = layout(
    row(
        column(
            row(
                column(
                    tools,
                    width=settings.TOOL_WIDTH
                ),
                choropleth(),
                height=settings.COL1_HEIGHT
            ),
            row(scatter(), height=settings.COL1_HEIGHT),
            width=settings.COL1_WIDTH
        ),
        column(
            row(line_chart(), height=settings.COL2_HEIGHT1),
            row(bar_chart_gender(), height=settings.COL2_HEIGHT2),
            row(bar_chart_level(), height=settings.COL2_HEIGHT2),
            width=settings.COL2_WIDTH
        )
    )
)

curdoc().add_root(dashboard)
curdoc().title = 'World Education Dashboard'
