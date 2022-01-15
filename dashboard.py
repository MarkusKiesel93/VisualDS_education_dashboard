from bokeh.transform import factor_cmap
from bokeh.models import Legend, LinearColorMapper
from bokeh.palettes import Category10, Greens9
from bokeh.layouts import column, row, layout
from bokeh.models import ColumnDataSource, GeoJSONDataSource, Slider, Select, ColorBar, CheckboxGroup
from bokeh.plotting import figure, curdoc

from data import get_merged_data, get_geo_data
from config import Config

# load datasets
df = get_merged_data(year_as_datetime=False)
df_geo = get_geo_data()

settings = Config(df)


def tocol(indicator, level=None, gender=None):
    if level and gender:
        levels = [indicator, level, gender]
    else:
        levels = [indicator, select_level.value, select_gender.value]
    return '_'.join(levels)

# define helper functions:
def select_range(config, indicator, level, gender):
    if config[indicator]['range'] == 'rate':
        min, max = 0, 105
    else:
        min = df[tocol(indicator, level, gender)].min() * 0.9
        max = df[tocol(indicator, level, gender)].max() * 1.1

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


def update_view(attr, old, new):
    dashboard.children[0].children[1] = scatter()
    dashboard.children[1] = choropleth()


def test(attr, old, new):
    print(new)
    print(source.to_df().iloc[new])


def update_data(attr, old, new):
    subset = df.xs(slider_year.value, level='year')
    subset_geo = df_geo.join(subset, on='country_code')
    source.data = subset
    geo_source.geojson = subset_geo.to_json()


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
    # todo: maybe use info items here as well
    tooltips = [(format_label(value), '@' + tocol(value)) for value in values]
    tooltips.insert(0, ('Country', '@country_name'))
    return tooltips


subset = df.xs(settings.DATES[-1], level='year')
subset_geo = df_geo.join(subset, on='country_code')
source = ColumnDataSource(subset)
geo_source = GeoJSONDataSource(geojson=subset_geo.to_json())

color_mapper = LinearColorMapper(palette=Category10[7])

# define widgets
slider_year = create_slider_widget('Year', settings.DATES)
select_indicator = create_select_widget('Indicator:', list(settings.INDICATORS.keys()))
select_by = create_select_widget('By:', list(settings.BY.keys()))
select_color = create_select_widget('Color by:', settings.COLOR_BY)
select_level = create_select_widget('Education Level:', create_options('level', settings.LEVELS))
select_gender = create_select_widget('Gender:', create_options('gender', settings.GENDER))
checkbox_group = create_checkbox_widget(['Log scale'], [0])

# add callbacks to widgets
slider_year.on_change('value', update_data)
select_indicator.on_change('value', update_view_tools)
select_by.on_change('value', update_view_tools)
select_color.on_change('value', update_view)
select_level.on_change('value', update_data)
select_gender.on_change('value', update_data)
checkbox_group.on_change('active', update_view)
source.selected.on_change('indices', test)

# scatterplot function
def scatter():
    fig = figure(
        height=400,
        width=800,
        tools='hover,tap,pan,box_zoom,wheel_zoom,zoom_in,zoom_out,lasso_select,save,reset',
        toolbar_location='above',
        x_axis_type='log' if 0 in checkbox_group.active else 'linear',
        y_range=select_range(settings.INDICATORS, select_indicator.value, select_level.value, select_gender.value),
        x_range=select_range(settings.BY, select_by.value, select_level.value, select_gender.value))
    fig.yaxis.axis_label = format_label(select_indicator.value)
    fig.xaxis.axis_label = format_label(select_by.value, x_label=True)
    fig.add_layout(Legend(), 'right')
    fig.legend.location = 'top_left'
    fig.legend.title = format_label(select_color.value)

    # set tooltips
    fig.hover.tooltips = create_tooltips([select_indicator.value, select_by.value])

    # create scatterplot
    fig.scatter(
        x=tocol(select_by.value),
        y=tocol(select_indicator.value),
        source=source,
        color=factor_cmap(
            field_name=select_color.value,
            palette=Category10[len(settings.GROUPS[select_color.value])],
            factors=settings.GROUPS[select_color.value]),
        size=9,
        hover_line_color='black',
        legend_group=select_color.value,
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
        fill_color={'field': tocol(select_indicator.value), 'transform': color_mapper},
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


# add tools and different plots to oune dashboard
tools = column(slider_year, select_indicator, select_by, select_level, select_gender, select_color, checkbox_group)
dashboard = layout(
    row(tools, scatter()),
    row(choropleth())
)

curdoc().add_root(dashboard)
curdoc().title = 'World Education Dashboard'
