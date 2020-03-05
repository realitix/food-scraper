from util import *
import json
from googletrans import Translator
import re


def run():
    aliment_files = set(listdir(path.join(HERE, 'cache', 'step3')))
    aliment_files = aliment_files - set(['traductions'])
    result = {
        'map': {},
        'categories_fr': {},
        'aliments': [],
        'timestamp': get_timestamp()
    }

    # Load aliments
    aliments = []
    for a in aliment_files:
        with open(path.join(HERE, 'cache', 'step3', a), 'r') as f:
            aliments.append(json.load(f))

    # Retrieve categories and nutrients to create id
    def add_in_map(map, elem):
        if elem not in map:
            map[elem] = len(map) + 1

    data_map = {}
    for a in aliments:
        add_in_map(data_map, a['category']) # category is in english
        for k, v in a['nutrition'].items():
            for e in v:
                nutrion_name = e['name']
                add_in_map(data_map, nutrion_name)
    result['map'] = data_map

    # Traduce categories in French
    try:
        with open(path.join(HERE, 'cache', 'step4', 'categories_traduction'), 'r') as f:
            cache_traduction = json.load(f)
    except:
        cache_traduction = {'': ''}

    translator = Translator()
    for k, v in result['map'].items():
        if k not in cache_traduction:
            trad = translator.translate(k, src='en', dest='fr')
            fr_val = trad.text
            cache_traduction[k] = fr_val
        else:
            fr_val = cache_traduction[k]
        result['categories_fr'][k] = fr_val

    with open(path.join(HERE, 'cache', 'step4', 'categories_traduction'), 'w') as f:
        json.dump(cache_traduction, f)

    # Add aliments to result
    for a in aliments:
        r = {}

        # id
        r['id'] = re.sub("[^0-9]", "", a['id'])

        # names
        r['names_en'] = []
        r['names_fr'] = []
        for n in a['name']:
            if n['lang'].lower().startswith('en'):
                r['names_en'].append((n['val'], n['rank']))
            if n['lang'].lower().startswith('fr'):
                r['names_fr'].append((n['val'], n['rank']))

        # category
        r['category_id'] = result['map'][a['category']]

        # measures
        r['measures'] = {}
        for m in a['measures']:
            r['measures'][m['name']] = m['value']

        # nutritions
        r['nutritions'] = {}
        for k, v in a['nutrition'].items():
            for e in v:
                r['nutritions'][result['map'][e['name']]] = {'val': e['value'], 'unit': e['unit']}
        
        # add to result
        result['aliments'].append(r)
    
    # Write file
    with open(path.join(HERE, 'cache', 'step4', 'out.json'), 'w') as f:
        json.dump(result, f)


