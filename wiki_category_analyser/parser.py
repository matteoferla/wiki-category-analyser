import warnings

import wikitextparser as wtp
import pageviewapi
import requests, re, csv
import datetime as dt
from typing import *
import mwxml, bz2

class WikicatParser:
    """
    Gets all the pages recursively within a category and parser the content (via a suplied function) and gets pageviews.

    .. code-block:: python
        pages = WikicatParser(cat_name, custom_page_parser=my_function, extra_fields=[], forbidden_categories_keywords=[...]).get_pages_recursively()
        print(pages.data)
        pandas.DataFrame.from_records(list(pages.data.values()))

    ``custom_page_parser`` is for content mining. a function that given wiki text returns a dictionary of whatever it mined.
    Any extra fields need to be added to extra_fields or to_csv will fail.

    ``.get_pages_recursively`` gets everything downwards. Do note that .forbidden_categories_keywords may need to be set.
    This calls both .get_pages and .get_subcategories, both of which actually call .get_members which calls get, which is the web fetcher.
    ``.get_pageviews`` gets the page views.
    """
    api = "https://en.wikipedia.org/w/api.php"

    def __init__(self, category,
                 no_views=False,
                 no_content=False,
                 custom_page_parser=None,
                 wanted_templates=None,
                 extra_fields=None,
                 forbidden_categories_keywords=None):
        self.session = requests.Session()
        self.no_views = no_views
        self.no_content = no_content
        self.data = {}
        if 'Category:' not in category:
            self.category = 'Category:' + category
        else:
            self.category = category
        self.category_map = {}
        self.category_cleaned = category.replace(' ', '_').replace('Category:', '')
        if custom_page_parser:
            self.page_parser = custom_page_parser
        elif wanted_templates:
            self.wanted_templates = wanted_templates
            self.page_parser = self.parse_templates
        else:
            self.no_content = True
            self.page_parser = lambda text: {}
        if extra_fields:
            self.extra_fields = extra_fields
        else:
            self.extra_fields = []
        if forbidden_categories_keywords:
            if isinstance(forbidden_categories_keywords, str):
                self.forbidden_categories_keywords = [self.forbidden_categories_keywords.lower()]
            else:
                self.forbidden_categories_keywords = [k.lower() for k in forbidden_categories_keywords]
        else:
            self.forbidden_categories_keywords = []

    def get(self, params):
        """
        Does the actual fetching
        Called by the methods ``get_content`` and ``get_members``
        which are for article pages and category pages respectively
        """
        data = self.session.get(url=self.api, params=params).json()
        if 'continue' in data:
            params['cmcontinue'] = data['continue']['cmcontinue']
            t = list(data['query'].keys())[0]
            new_data = self.get(params)
            new_data['query'][t] = [*data['query'][t], *new_data['query'][t]]
            data = new_data
        return data

    def _add_datum(self, data, cat):
        """
        Fills the data e
        """
        for d in data:
            name = d["title"]
            if name not in self.data:
                self.data[name] = d
                self.data[name]['category'] = cat
                if not self.no_views:
                    self.data[name]['views'] = self.get_pageviews(name)
                if not self.no_content:
                    wiki = self.get_content(name)
                    for key, value in self.page_parser(wiki).items():
                        self.data[name][key] = value
            elif cat in self.data[name]["category"].split('|'):
                warnings.warn('dejavu: requested visited article for already visited category')
            else:
                self.data[name]["category"] += '|' + cat

    def get_subcategories(self, cat):
        subcats = []
        for subcat in self.get_members(cat, 'subcat'):
            for k in self.forbidden_categories_keywords:
                if k in subcat['title'].lower():
                    print(f'BAN: {subcat["title"]} removed because it contained {k}')
                    break
            else:
                subcats.append(subcat)
        self.category_map[cat] = [s['title'] for s in subcats]
        return subcats

    def get_page_by_name(self, name, cat='Manual') -> dict:
        """
        Gets the page by the name specified.
         This is for user fixes etc.
        """
        self._add_datum([{'title': name}], cat)
        return self.data[name]

    def get_pages(self, cat: str):
        """
        gets all the pages within the category
        """
        return self.get_members(cat, 'page')

    def get_members(self, cat, cmtype='subcat|page'):
        """
        Get the members of a given category and fill the internal ``data`` attribute
        """
        params = {
            'action':  "query",
            'list':    "categorymembers",
            'cmtitle': cat,
            'cmtype':  cmtype,
            'cmdir':   "desc",
            'format':  "json"
        }
        r = self.get(params)
        if 'query' not in r:
            print(f'{cat} replied with {str(r)}.')
            return []
        member_info = r['query']['categorymembers']
        self._add_datum(member_info, cat)
        return member_info

    def get_pages_from_dump(self, dump_path: str='enwiki-latest-pages-articles.xml.bz2'):
        """
        https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2
        """
        dump = mwxml.Dump.from_file(bz2.open(dump_path,
                                             mode='rt', encoding='utf-8')
                                   )
        assert self.wanted_templates, 'Template needs to be specified.'
        wanted = [w.lower() for w in self.wanted_templates]
        for page in dump:
            revision = next(page)
            if revision.text is None:
                continue
            lower_text = revision.text.lower()
            if not any([want in lower_text for want in wanted]):
                continue
            self._add_datum([{'title': page.title}], 'dump')

    def get_pages_recursively(self, cat=None):
        if cat is None:
            cat = self.category
        subcats = [s['title'] for s in self.get_subcategories(cat)]
        data = self.get_pages(cat)
        for c in subcats:
            ndata = self.get_pages_recursively(c)
            print(f'{c} has {len(data)} pages directly and {len(ndata)} in subcategories')
            data.extend(ndata)
        return data

    def get_pageviews(self, page: str, frequency: str = 'monthly', days_ago: str = 365) -> float:
        yesterday: dt.date = dt.date.today() - dt.timedelta(days=1)
        yesteryear: dt.date = dt.date.today() - dt.timedelta(days=days_ago + 1)
        format_day: Callable[[dt.date], str] = lambda d: f'{d.year}{d.month:0>2}{d.day:0>2}00'
        try:
            views = pageviewapi.per_article('en.wikipedia',
                                            page,
                                            format_day(yesteryear),
                                            format_day(yesterday),
                                            access='all-access', agent='all-agents', granularity='monthly')
            if 'items' in views:
                return sum([view['views'] for view in views['items']]) / len(views['items'])
            else:
                print('error', page, views)
                return float('nan')
        except pageviewapi.client.ZeroOrDataNotLoadedException:
            return float('nan')

    def get_content(self, page) -> str:
        """
        Gets the content of a given article
        """
        params = {
            'action':    "query",
            'prop':      'revisions',
            'rvprop':    'content',
            'rvsection': 0,
            'titles':    page,
            'format':    "json"
        }
        data = self.session.get(url=self.api, params=params).json()
        pageid = list(data['query']['pages'].keys())[0]
        wikimarkup:str = data['query']['pages'][pageid]['revisions'][0]['*']
        return wikimarkup.encode('utf-8', 'ignore').decode('unicode_escape', 'ignore')  # not quite right

    ####### code to convert template to dictionary
    def parse_templates(self, text: str) -> dict:
        """
        Convert template to dictionary
        """
        dex = {}
        for t in wtp.parse(text).templates:
            for want in self.wanted_templates:
                if want.lower() in t.normal_name().lower():  # not using t.name has training space.
                    dex = {**dex, **self._template_to_dict(t)}
        return dex

    def _arg_to_val(self, arg):
        val = arg.value
        for t in arg.templates:
            if t.arguments:
                tval = t.arguments[0].value
                if t.normal_name() in ('nowrap', 'val'):
                    if any(['ul' in a.name for a in t.arguments]):  # unit!
                        tval += [a.value for a in t.arguments if 'u' in a.name][0]  # u= and ul=
                    val = val.replace(t.string, tval)
        val = re.sub('<.*?\/>', '', val)  # remove self closing tags
        val = val.replace('&nbsp;', ' ')
        val = re.sub('<.*?>.*?<\/.*?>', '', val)  # remove tags
        val = re.sub('<!--.*?-->', '', val)  # remove comments
        val = val.replace('–', '-')  # en dash to hyphen minus
        val = val.replace('–', '-')  # em dash to hyphen minus
        val = re.sub('±\s+\d+\.?\d*', '', val)  # clear error for safety
        val = val.rstrip().lstrip()
        return val

    def _arg_to_key(self, arg):
        return arg.name.rstrip().lstrip()

    def _template_to_dict(self, template):
        return {self._arg_to_key(arg): self._arg_to_val(arg) for arg in template.arguments}

    # -------------- IO ----------------------------

    def to_dataframe(self):
        import pandas as pd
        return pd.DataFrame.from_dict(self.data, orient='index')

    def to_csv(self):
        """Don't save as csv for storage. Save as pickle. This is just for causal inspection in Excel."""
        with open(f'{self.category_cleaned}.csv', 'w', newline='') as w:
            dw = csv.DictWriter(w, ['title', 'category', 'ns', 'views', 'pageid'] + self.extra_fields,
                                extrasaction='ignore')
            dw.writeheader()
            dw.writerows(self.data.values())
        return self
