# Visual Data Science

## Topic:
### How has the level of education changed in different countries?

## Datasets.
World Bank: https://data.worldbank.org/topic/education
https://datacatalog.worldbank.org/search/dataset/0038001/Harmonized-Learning-Outcomes--HLO--Database

https://www.rug.nl/ggdc/historicaldevelopment/maddison/releases/maddison-project-database-2020

convert to pdf:
jupyter nbconvert --to pdf --no-input *.ipynb

teachers_primary_total - teachers_primary_female
1 - education_pupils_primary_female
1 - education_pupils_secondary_female

# run boke server
bokeh serve --show myapp.py

ToDos:
* make year selection a range or a point
* callbacks for tab and hover