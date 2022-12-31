The codebase here uses the [module pageviewapi](https://github.com/Commonists/pageview-api.git),
which queries each page, while if there is a large dataset it pays to download the data and parse.

For example, below the hours visits for a given month for each day are combined if the wikipedia `en` edition. 

```python
yyyy = '2022'
mm = '07'
yyyymm = yyyy + mm
import requests, os, gzip, pickle
from collections import defaultdict
index_page = f'https://dumps.wikimedia.org/other/pageviews/{yyyy}/{yyyy}-{mm}/'

import requests
import bs4
import json

response: requests.Response = requests.get(index_page)
soup = bs4.BeautifulSoup(response.text, 'html.parser')
pages = {tag.text: index_page+tag['href'] for tag in soup.find_all('a') if tag.text != '../'}

for i in range(1, 31):
    combo_path = os.path.join('extracted_dumps', f'pageviews-{yyyymm}.p')
    if os.path.exists(combo_path):
        continue
    for p in range(0, 23):
        page = f'pageviews-{yyyymm}{i:0>2}-{p:0>2}0000.gz'
        if page not in pages:
            continue
        path = os.path.join('dumps', page)
        if os.path.exists(path):
            continue
        href = pages[page]
        with open(path, 'wb') as fh:
            fh.write(requests.get(href, stream=True).content)
    # combine
    counts = defaultdict(int) # per day summa hours
    for p in range(0, 23):
        path = os.path.join('dumps', f'pageviews-{yyyymm}{i:0>2}-{p:0>2}0000.gz')
        with gzip.open(path, mode='rt', encoding='utf8') as fh:
            for line in fh:
                parts = line.split()
                if len(parts) != 4:
                    continue # encoding error
                domain_code, page_title, count_views, total_response_size = parts
                if domain_code != 'en':
                    continue
                if ':' in page_title:
                    continue
                counts[page_title] += int(count_views) 
        os.remove(path)
    with open(combo_path, 'wb') as fh:
        pickle.dump(counts, fh)
        
        
import json, gzip

with gzip.open(os.path.join('extracted_dumps', f'pageviews-{yyyymm}.json.gz'), mode='wt', encoding='utf8') as fh:
    json.dump(counts, fh)
```
