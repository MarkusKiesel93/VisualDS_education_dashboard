from bokeh.transform import factor_cmap
from bokeh.models import Legend, LinearColorMapper, CategoricalColorMapper
from bokeh.palettes import Category10, Greens9
from bokeh.layouts import column, row, layout
from bokeh.models import ColumnDataSource, GeoJSONDataSource, Slider, Select, ColorBar, CheckboxGroup, Selection
from bokeh.plotting import figure, curdoc
from bokeh.transform import dodge
import pandas as pd
from data import get_merged_data, get_geo_data
from config import Config

# load datasets
df = get_merged_data()
df_geo = get_geo_data()

settings = Config(df)


def indicator_col(indicator=None, level=None, gender=None):
    if not indicator:
        indicator = select_indicator.value
    if not level:
        level = select_level.value
    if not gender:
        gender = select_gender.value
    return '_'.join([indicator, level, gender])


# define helper functions:
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
    options = [(option, format_label(option)) for option in options]
    return Select(
        title=title,
        value=value,
        options=options
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


def geo_index(selected_countries):
    index = []
    geo_country_codes = list(subset_geo.reset_index()['country_code'].values)
    for country in selected_countries:
        index.append(geo_country_codes.index(country))
    return index


def update_view(attr, old, new):
    dashboard.children[0].children[1] = scatter()
    dashboard.children[0].children[2] = line_chart()
    dashboard.children[1].children[0] = choropleth()
    dashboard.children[1].children[1] = bar_chart_gender()
    dashboard.children[1].children[2] = bar_chart_level()


def test(attr, old, new):
    data = source.to_df().iloc[new]
    selected_countries = data['country_code'].values
    dashboard.children[0].children[2] = line_chart(selected_countries)
    dashboard.children[1].children[1] = bar_chart_gender(data)
    dashboard.children[1].children[2] = bar_chart_level(data)
    geo_source.selected.indices = geo_index(selected_countries)


# todo callbach for clicking map
def test2(attr, old, new):
    print(new)


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
    select_level.options = level_options
    select_level.value = level_options[0]
    gender_options = create_options('gender', settings.GENDER)
    select_gender.options = gender_options
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
source.selected.on_change('indices', test)
geo_source.selected.on_change('indices', test2)

# scatterplot function
def scatter():
    fig = figure(
        height=400,
        width=800,
        tools='hover,tap,pan,box_zoom,wheel_zoom,zoom_in,zoom_out,lasso_select,save,reset',
        toolbar_location='above',
        x_axis_type='log' if 0 in checkbox_group.active else 'linear',
        y_range=select_range(settings.INDICATORS, select_indicator.value),
        x_range=select_range(settings.BY, select_by.value))
    fig.yaxis.axis_label = format_label(select_indicator.value)
    fig.xaxis.axis_label = format_label(select_by.value, x_label=True)
    fig.add_layout(Legend(), 'right')
    fig.legend.title = format_label(select_group.value)

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
        fill_color={'field': indicator_col(select_indicator.value), 'transform': color_mapper},
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


# todo: create line_chart for goups by default and if selected create for each country
def line_chart(countries=[]):
    fig = figure(
        plot_height=300,
        plot_width=700,
        x_range=(settings.DATES[0], settings.DATES[-1]),
        y_range=select_range(settings.INDICATORS, select_indicator.value),
        title='Development by Year'
    )
    fig.xaxis.axis_label = 'Year'
    fig.yaxis.axis_label = format_label(select_indicator.value)
    fig.add_layout(Legend(), 'right')
    fig.legend.title = format_label(select_group.value)

    # todo: move to somewhere general
    color_mapper = CategoricalColorMapper(
        palette=Category10[len(settings.GROUPS[select_group.value])],
        factors=settings.GROUPS[select_group.value]
    )

    def get_color(group):
        return color_mapper.palette[color_mapper.factors.index(group)]

    if len(countries) < 1:
        data = df.groupby([select_group.value, 'year']).mean().reset_index()
        for group in settings.GROUPS[select_group.value]:
            fig.line(
                'year',
                indicator_col(),
                source=ColumnDataSource(data[data[select_group.value] == group]),
                color=get_color(group),
                legend_group=select_group.value,
            )

    else:
        for country in countries:
            fig.line('year', 'learning_outcome_total_total', source=ColumnDataSource(df.xs(country, level='country_code')))

    return fig


def bar_chart_gender(data=pd.DataFrame()):
    dodge_values = [-0.25, 0.0, 0.25]
    
    if data.shape[0] < 1:
        source = ColumnDataSource(df.xs(slider_year.value, level='year')
                                  .groupby([select_group.value]).mean().reset_index())

        fig = figure(
            x_range=source.data[select_group.value],
            y_range=(0, select_range(settings.INDICATORS, select_indicator.value)[1]),
            title='todo',
            height=350,
            toolbar_location=None,
            tools=""
        )
        fig.xaxis.major_label_orientation = 120

        # todo: only use possible values
        for gender, d in zip(settings.GENDER, dodge_values):
            fig.vbar(
                x=dodge(select_group.value, d, range=fig.x_range),
                top=indicator_col(gender=gender),
                source=source,
                width=0.2,
                color=settings.GENDER_COLORS[gender],
                legend_label=format_label(gender)
            )

    else:
        fig = figure(
            x_range=data['country_name'],
            y_range=(0, 700),
            title='todo',
            height=350,
            toolbar_location=None,
            tools=""
        )
        fig.xaxis.major_label_orientation = 120

        source = ColumnDataSource(data=data)
        for gender, d in zip(settings.GENDER, dodge_values):
            fig.vbar(
                x=dodge('country_name', d, range=fig.x_range),
                top=indicator_col(gender=gender),
                source=source,
                width=0.2,
                color=settings.GENDER_COLORS[gender],
                legend_label=format_label(gender)
            )

    return fig


# todo change gender by selection
def bar_chart_level(data=pd.DataFrame()):
    dodge_values = [-0.2, -0.1, 0.1, 0.2]

    if data.shape[0] < 1:
        source = ColumnDataSource(df.xs(slider_year.value, level='year')
                                  .groupby([select_group.value]).mean().reset_index())

        fig = figure(
            x_range=source.data[select_group.value],
            y_range=(0, select_range(settings.INDICATORS, select_indicator.value)[1]),
            title='todo',
            height=350,
            toolbar_location=None,
            tools=""
        )
        fig.xaxis.major_label_orientation = 120

        # todo: only use possible values
        for level, d in zip(settings.LEVELS, dodge_values):
            fig.vbar(
                x=dodge(select_group.value, d, range=fig.x_range),
                top=indicator_col(level=level),
                source=source,
                width=0.2,
                color=settings.LEVEL_COLORS[level],
                legend_label=format_label(level)
            )
    else:
        fig = figure(
            x_range=data['country_name'],
            y_range=(0, 700),
            title='todo',
            height=350,
            toolbar_location=None,
            tools=""
        )
        fig.xaxis.major_label_orientation = 120

        source = ColumnDataSource(data=data)

        # todo: only use possible values
        for level, d in zip(settings.LEVELS, dodge_values):
            fig.vbar(
                x=dodge('country_name', d, range=fig.x_range),
                top=indicator_col(level=level),
                source=source,
                width=0.2,
                color=settings.LEVEL_COLORS[level],
                legend_label=format_label(level)
            )

    return fig


# add tools and different plots to oune dashboard
tools = column(slider_year, select_indicator, select_by, select_level, select_gender, select_group, checkbox_group)
dashboard = layout(
    row(tools, scatter(), line_chart()),
    row(choropleth(), bar_chart_gender(), bar_chart_level()),
)

curdoc().add_root(dashboard)
curdoc().title = 'World Education Dashboard'

# todo: title by section
# todo: resize sections and give fixed size
