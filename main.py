#!/usr/bin/env python3
import asyncio
from util import init_browser, patch_pyppeteer
from step1 import get_all_aliments_in, find_max_aliments
from step2 import get_aliments_to_retrieve, retrieve
from step3 import traduce_all_aliments



async def main():
    patch_pyppeteer()

    print("-------------------------")
    print("Task 0 - Init browser")
    browser = await init_browser()

    print("-------------------------")
    print("Task 1 - Search aliments")
    list_aliment_in = get_all_aliments_in()
    await find_max_aliments(list_aliment_in, browser)

    print("-------------------------")
    print("Task 2 - Get aliment detail")
    aliments_to_retrieve = get_aliments_to_retrieve()
    await retrieve(aliments_to_retrieve, browser)

    print("-------------------------")
    print("Task 3 - Traduce")
    traduce_all_aliments()

    
    

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())