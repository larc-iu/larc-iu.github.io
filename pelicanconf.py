import datetime

CURRENT_YEAR = datetime.datetime.now().year

AUTHOR = 'LARC Group'
SITENAME = 'LARC'
SITEURL = "https://larc-iu.github.io"

# Basic configuration
PATH = "content"
TIMEZONE = 'America/New_York'
DEFAULT_LANG = 'en'

# Disable all feed generation
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Remove unused blog features
LINKS = ()
SOCIAL = ()
DEFAULT_PAGINATION = False
RELATIVE_URLS = True

# Static content handling
STATIC_PATHS = ['static', 'images']
STATIC_SAVE_AS = '{path}'
STATIC_URL = '{path}'

# Markdown extensions. This restates Pelican's defaults because setting
# MARKDOWN replaces them wholesale rather than merging: 'extra' is what gives
# us tables and definition lists, 'meta' parses the Title:/Date: headers, and
# 'smarty' turns straight quotes, apostrophes and '--' into their typographic
# equivalents in body text.
MARKDOWN = {
    'extension_configs': {
        'markdown.extensions.codehilite': {'css_class': 'highlight'},
        'markdown.extensions.extra': {},
        'markdown.extensions.meta': {},
        'markdown.extensions.smarty': {},
    },
    'output_format': 'html5',
}

# Shared plugins, installed from github.com/larc-iu/larc-site-utils. They only
# hand data to templates, so all the rendering lives in themes/academic.
PLUGINS = [
    'larc_site_utils.yaml_data',
    'larc_site_utils.publications',
    'larc_site_utils.news',
]

# Publications. Everyone on the people page is highlighted in author lists, so
# a new member's papers start standing out the moment they are added to
# people.yaml -- there is no second list of names to keep in sync.
PUBLICATIONS_BIB = 'static/publications.bib'
HIGHLIGHT_AUTHORS_FROM_YAML = 'people'
# Show work from 2024 onward. Earlier entries stay in the .bib rather than
# being deleted, so moving or lifting the cutoff later is a one-line change.
PUBLICATIONS_MIN_YEAR = 2024

# Turn off default templates (including index)
DIRECT_TEMPLATES = []

# Site navigation, rendered by themes/academic/templates/base.html
MENUITEMS = (
    ('About', '/index.html'),
    ('People', '/people.html'),
    ('Projects', '/projects.html'),
    ('Publications', '/publications.html'),
    ('News', '/news.html'),
)

# Disable categories and tags
CATEGORY_SAVE_AS = ''
AUTHOR_SAVE_AS = ''
TAG_SAVE_AS = ''

# Everything is a page except news/, which holds dated articles. The folder
# name becomes the category, which is how templates tell the two apart.
ARTICLE_PATHS = ['news']
PAGE_PATHS = ['']
PAGE_EXCLUDES = ['news']

# How much news the home page shows: at most HOME_NEWS_MAX posts, and none
# older than HOME_NEWS_MONTHS, so the section empties itself during quiet
# stretches instead of showing something stale.
HOME_NEWS_MAX = 3
HOME_NEWS_MONTHS = 6

# URL and path configurations.
#
# The category group is what makes an article in content/news/ come out with
# category 'news', which is how templates tell news apart from pages. Pelican
# normally derives that from the folder name, but since 4.12 it only does so
# when CATEGORY_SAVE_AS is truthy (readers.py, USE_FOLDER_AS_CATEGORY), and we
# set that empty to suppress category pages. Without this, articles have no
# category attribute at all: category-filtered lists come out empty and
# building a draft raises AttributeError. Capturing it here works the same on
# either side of that change.
PATH_METADATA = r'(?P<path_no_ext>(?:(?P<category>[^/]+)/)?.*)\..*'
SLUG_REGEX_SUBSTITUTIONS = [(r'[^\w/]+', '-')]
PAGE_URL = '{path_no_ext}.html'
PAGE_SAVE_AS = '{path_no_ext}.html'
ARTICLE_URL = '{path_no_ext}.html'
ARTICLE_SAVE_AS = '{path_no_ext}.html'
DEFAULT_DATE_FORMAT = '%B %d, %Y'
INDEX_URL = '{path_no_ext}/index.html'
INDEX_SAVE_AS = '{path_no_ext}/index.html'

# Use basename for slug generation
SLUGIFY_SOURCE = 'basename'

# Use path as translation identifier
TRANSLATION_ID_METADATA = 'path'

# Field formatting
FORMATTED_FIELDS = ['summary', 'path', 'url', 'save_as']

# Theme
THEME = 'themes/academic'
