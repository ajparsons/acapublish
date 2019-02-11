# Acapublish

Set of scripts to assist in development of papers.

Converts Scrivner and Google Docs projects to markdown - which can then be converted to pdf (via LaTex).

Uses fabric as a script management tool - to render a project run ```fab compile```.

See [] for a blank project template. 

## Citation Format

Uses a format agnostic citation system for later ease of conversion. A bibtex file is then used to generate full references.

Blah Blah [#smith2018;p.217] - (Smith, 2018) or 'Blah Blah ^1'

As [#*smith2018] said - 'As Smith (2018) said' or 'As Smith^1 said' depending on selected citation format. 

[#**smith2018] will just return the year - for handing citations after quotes when quoting the same author more than once in a sentence. 

The specification of a two columned spreadsheet OVERRIDE_FILE in the settings will let you customise exact bibliographic referencing beyond that produced by the bibtex reader.

The settings file of the project contains additional formatting options:

```
INITIAL_QUOTES = SINGLE
DOCX_TEMPLATE = r"_templates\parliamentary_affairs.docx"

# REFERENCING

SHORT_CITE = True
SEPERATE_TABLES = True

if SHORT_CITE:
    CITESTYLE = "authoryear-comp"  # "verbose-trad2" #biblatex style
    REFS_IN_SENTENCE = INSIDE
    MARKDOWN_CITE = "harvard-cite-them-right"
else:
    CITESTYLE = "authoryear-comp"  # "verbose-trad2" #biblatex style
    REFS_IN_SENTENCE = OUTSIDE
    MARKDOWN_CITE = "oxford-art-journal"  # "chicago-fullnote-bibliography"
```

The above will adjust all quotes to be single quotes (and adjust nested quotes so that that the internal quotes are double). A particular template is used for producing DOCX files, tables are exported as a seperate document and references are moved to inside sentences.

This last point means that

>"Quote!" [#Smith2017;]

can be either 

>"Quote!"(Smith 2018).

or 

>"Quote!".^1

## Tables

Tables are expected in a markdown format and are lettered rather than numbered. These will be numbered during the final render. 

```
| Predictor Variables    | Model 1       | Model 2       |
|:-----------------------|:--------------|:--------------|
| (Constant)             | 48.11***      | 48.55***      |
|                        | [42.04,55.06] | [42.02,55.08] |
| Age                    | 0.14          | 0.14          |
|                        | [-0.00,0.28]  | [-0.00,0.28]  |
| Gender                 | -7.12***      | -7.21***      |
| (0 = Male, 1 = Female) | [-9.76,-4.67] | [-9.78,-4.64] |
| No. of Emails          | 0.01***       | 0.01***       |
|                        | [0.00,0.01]   | [0.00,0.01]   |
| Time in Parliament     | -0.14         | -0.15         |
| (years)                | [-0.31,0.02]  | [-0.31,0.02]  |
| Government Seat        | -             | -0.85         |
|                        |               | [-2.66,0.96]  |
| Constituency Seat      | -             | -             |
|                        |               |               |
| Adjusted R2            | 0.04          | 0.04          |
| Change in R2           | -             | -0.00         |
| N                      | 2,146         | 2,146         |
[Westminster Regression Model-sigtable3][table-r]
```

This can be referenced in text as "As shown in Table [ref:table-r]." - which will become 'Table 1'. 

The title of the table will be 'Westminster Regression Model' - '-sigtable3' indicates it should include a key beneath indicating which p-values up to 3* mean.

## Gender report

The compile process creates various metric of gender citation:

| Count                            | male        | female      | unknown | initial | ratio       |
|----------------------------------|-------------|-------------|---------|---------|-------------|
| all authors (all citations)      | 66          | 16          |         |         | 19.51       |
| all authors (unique documents)   | 42          | 9           |         |         | 17.65       |
| first authors (all citations)    | 39          | 11          |         |         | 22          |
| first authors (unique documents) | 24          | 6           |         |         | 20          |
| unique authors                   | 37          | 9           |         |         | 19.57       |
| Year Difference                  | 2003.547619 | 2008.222222 |         |         | 4.674603175 |


In the outputs folder, the compile process will export two files - the results table above and how it is catagorising individual authors. These can be overriden by passing back in a two columned spreadsheet specified by the GENDER_OVERRIDE setting.

By default the gender detector assumes the setting is 'uk' - this can be adjused using the GENDER_LOCALE setting.