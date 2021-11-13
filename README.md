# wiki-category-analyser
Given a Wikipedia category and some infobox names, make a table of all the page within that category with fields from the infobox.
Basically, it's a tool to datamine Wikipedia. This is mostly the same code as used in:

* https://github.com/matteoferla/Wikipedia_star
* https://github.com/matteoferla/Wikipedia_Mars
* https://github.com/matteoferla/Wikipedia_dinosaurs
* https://github.com/matteoferla/Wikipedia_planes

## Usage

    pages = WikicatParser(category_name)
    pages.get_pages_recursively()
    
    print(pages.data) # dict of page names --> data
    table = pages.to_dataframe()
    
    
    no_views=False,
                 no_content=False,
                 custom_page_parser=None,
                 wanted_templates=None,
                 extra_fields=None,
                 forbidden_categories_keywords=None
    
    
    
    >>>
