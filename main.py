#!/usr/bin/env python3
from util import *


def main():
    patch_pyppeteer()
    list_aliment_in = get_all_aliments_in()
    find_max_aliments(list_aliment_in)
    aliments_to_retrieve = get_aliments_to_retrieve()

    slash = 0
    for a in aliments_to_retrieve:
        if '/' in a:
            slash +=1
            #print(a)

    print("simple quote: "+str(slash))

    retrieve(aliments_to_retrieve)
    

if __name__ == '__main__':
    main()