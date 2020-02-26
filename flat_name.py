import xmltodict
from os import path

HERE = path.dirname(path.abspath(__file__))


def main():
    alim_out = {}
    with open(path.join(HERE, "aliment_list.xml"), 'rb') as f:
        r = f.read()
        alim_out.update(xmltodict.parse(r)['TABLE'])

    result = set()
    for a in alim_out['ALIM']:
        result.add(a['alim_nom_eng'])
        result.add(a['alim_nom_index_eng'])

    with open(path.join(HERE, "alim_list_in.txt"), "w") as f:
        for r in result:
            f.write(r)
            f.write('\n')

if __name__ == '__main__':
    main()