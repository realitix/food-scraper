from util import *
import json
from googletrans import Translator
import re


def run():
    aliment_files = set(listdir(path.join(HERE, 'cache', 'step3')))
    aliment_files = aliment_files - set(['traductions'])
    result = {
        'aliments': [],
        'timestamp': get_timestamp()
    }

    # Load aliments
    aliments = []
    for a in aliment_files:
        with open(path.join(HERE, 'cache', 'step3', a), 'r') as f:
            aliments.append(json.load(f))

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
        r['category'] = a['category']

        # measures
        r['measures'] = []
        for m in a['measures']:
            r['measures'].append((m['name'], m['value']))

        # nutritions
        r['nutritions'] = []
        for k, v in a['nutrition'].items():
            for n in v:
                r['nutritions'].append(n)
        
        # add to result
        result['aliments'].append(r)
    
    # Write file
    with open(path.join(HERE, 'cache', 'step4', 'out.json'), 'w') as f:
        json.dump(result, f)

    # For references
    # Write category list, unit list, nutrient list
    result2 = {'units': [], 'categories': [], 'nutrients': []}
    for a in result['aliments']:
        if a['category'] not in result2['categories']:
            result2['categories'].append(a['category'])
        for m in a['measures']:
            if m[0] not in result2['units']:
                result2['units'].append(m[0])
        for n in a['nutritions']:
            if n['name'] not in result2['nutrients']:
                result2['nutrients'].append(n['name'])
            
    with open(path.join(HERE, 'cache', 'step4', 'references.json'), 'w') as f:
        json.dump(result2, f, indent=4, sort_keys=True)


