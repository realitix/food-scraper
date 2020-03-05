#!/usr/bin/env python3
import asyncio
from util import init_browser, patch_pyppeteer
import step1, step2, step3, step4, step5



async def main():
    patch_pyppeteer()

    print("-------------------------")
    print("Task 0 - Init browser")
    browser = await init_browser()

    print("-------------------------")
    print("Task 1 - Search aliments")
    await step1.run(browser)

    print("-------------------------")
    print("Task 2 - Get aliment detail")
    await step2.run(browser)

    print("-------------------------")
    print("Task 3 - Traduce all aliments")
    step3.run()

    print("-------------------------")
    print("Task 4 - Generate the final json")
    step4.run()

    print("-------------------------")
    print("Task 5 - Compress Json File")
    step5.run()

    
    

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())