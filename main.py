#!/usr/bin/env python3
from util import *


def main():
    #asyncio.get_event_loop().run_until_complete(test())
    #breakpoint()
    list_aliment_in = get_all_aliments_in()
    find_max_aliments(list_aliment_in)
    


if __name__ == '__main__':
    main()