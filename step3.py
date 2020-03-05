import json
from googletrans import Translator
from util import *


def traduce(translator, to_traduce, src, dst):
    if not to_traduce:
        return {}

    res = translator.translate('\n'.join(to_traduce), src=src, dest=dst)
    lines = res.text.splitlines()
    if len(lines) != len(to_traduce):
        print("Error: Number of line traduced not the same as the requested number of line to traduce")
        return {}

    return zip(to_traduce, lines)


def slen(a):
    return len('\n'.join(a))


def get_full_name(lang):
    for a in listdir(path.join(HERE, 'cache', 'step2')):
        with open(path.join(HERE, 'cache', 'step2', a), 'r') as f:
            content = json.load(f)
            for x in content['name']:
                if x['lang'].lower().startswith(lang):
                    return x['lang']


def run():
    aliments_in = set(listdir(path.join(HERE, 'cache', 'step2')))
    aliments_in = aliments_in - set(['non-existent'])
    alims_in = set()
    cached_aliments = set(listdir(path.join(HERE, 'cache', 'step3')))
    alims_in = aliments_in - cached_aliments
    translator = Translator()


    # First load traduction cache
    try:
        with open(path.join(HERE, 'cache', 'step3', 'traductions'), "r") as f:
            content = json.load(f)
            en_to_fr = content['en_to_fr']
            fr_to_en = content['fr_to_en']
    except FileNotFoundError:
        en_to_fr = {}
        fr_to_en = {}

    to_traduce_en = []
    to_traduce_fr = []
    max_len = 5000
    nb_traductions = 0
    for a in alims_in:
        with open(path.join(HERE, 'cache', 'step2', a), 'r') as f:
            content = json.load(f)
            names_en = [x['val'] for x in content['name'] if x['lang'].lower().startswith('en') and x['val'] not in en_to_fr]
            names_fr = [x['val'] for x in content['name'] if x['lang'].lower().startswith('fr') and x['val'] not in fr_to_en]

            if slen(to_traduce_en) + slen(names_en) > 5000:
                en_to_fr.update(traduce(translator, to_traduce_en, 'en', 'fr'))
                to_traduce_en = []

            if slen(to_traduce_fr) + slen(names_fr) > 5000:
                fr_to_en.update(traduce(translator, to_traduce_fr, 'fr', 'en'))
                to_traduce_fr = []

            to_traduce_en.extend(names_en)
            to_traduce_fr.extend(names_fr)
            nb_traductions += len(names_en) + len(names_fr)
    
    if to_traduce_en:
        en_to_fr.update(traduce(translator, to_traduce_en, 'en', 'fr'))
    if to_traduce_fr:
        fr_to_en.update(traduce(translator, to_traduce_fr, 'fr', 'en'))

    with open(path.join(HERE, 'cache', 'step3', 'traductions'), "w") as f:
        result = {'en_to_fr': en_to_fr, 'fr_to_en': fr_to_en}
        json.dump(result, f)

    print(f"{nb_traductions} traductions are done, now writing new file")

    full_name_fr = get_full_name('fr')
    full_name_en = get_full_name('en')
    for a in alims_in:
        with open(path.join(HERE, 'cache', 'step2', a), 'r') as f:
            content = json.load(f)
            add_to_content = []
            for x in content['name']:
                # Embedded lang are better so rank 1
                x['rank'] = 1

                if x['lang'].lower().startswith('en'):
                    add_to_content.append({'lang': full_name_fr, 'val': en_to_fr[x['val']], 'rank': 2})

                if x['lang'].lower().startswith('fr'):
                    add_to_content.append({'lang': full_name_en, 'val': fr_to_en[x['val']], 'rank': 2})
            content['name'].extend(add_to_content)
            
            with open(path.join(HERE, 'cache', 'step3', a), 'w') as f:
                json.dump(content, f)