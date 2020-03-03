from util import *


async def getResults(page):
    elements = await page.querySelectorAll(SRC_TABLE_ALL_RESULT)
    all_names = []
    
    if len(elements) == 1:
        return all_names
    
    for e in elements:
        div = await e.querySelector(SRC_TABLE_COL_NAME)
        val = await page.evaluate("el => el.textContent", div)
        if val != "Description":
            all_names.append(val)
    return all_names  


async def consume_aliment_to_search(queue):
    def write_to_cache(aliment, results):
        with open(path.join(HERE, 'cache', 'step1', aliment), "w") as f:
            for r in results:
                f.write(r)
                f.write('\n')

    page = await init_page(browser)
    try:
        await goToFoodSearch(page)
        await openSearchBox(page)

        while True:
            try:
                aliment = await queue.get()
                print(f"Search aliment: {aliment}")

                await search(page, aliment)
                all_results = await getResults(page)
                write_to_cache(aliment, all_results)
                await page.waitFor(500)
            except asyncio.CancelledError:
                print("consumer STOP")
                await page.close()
            except Exception as e:
                print(f"Stacktrace for aliment {aliment}")
                traceback.print_exc()
            else:
                queue.task_done()
    except Exception as e:
        print(e)

    await page.close()


def get_all_aliments_in():
    '''Get all aliments before asking'''
    def add_result(result, a):
        result.add(a)
        for x in (',', '('):
            result.add(a.split(x)[0])

    alims = {}
    with open(path.join(HERE, "aliment_list.xml"), 'rb') as f:
        r = f.read()
        alims.update(xmltodict.parse(r)['TABLE'])

    result = set()
    for a in alims['ALIM']:
        add_result(result, a['alim_nom_eng'])
        add_result(result, a['alim_nom_index_eng'])

    return result


async def find_max_aliments(aliments_in, browser):
    '''Find the maximum of aliment by using
    web browser to search for others aliments'''
    # Remove forbidden / char
    alims_in = {x.replace('/', ' ') for x in aliments_in}

    # Remove all aliment ever in the cache (step1)
    cached_aliments = set(listdir(path.join(HERE, 'cache', 'step1')))
    stills_alim = alims_in - cached_aliments

    print(f"Aliments left: {len(stills_alim)}")

    # Start the search process    
    if len(stills_alim) > 0:
        queue = asyncio.Queue()
        producer = produce_aliment_to_search(queue, stills_alim)
        consumers = [asyncio.create_task(consume_aliment_to_search(queue, browser)) for _ in range(NB_PROCESS)]
        for completed in asyncio.as_completed([producer, *consumers]):
            await completed
            break

        await queue.join()
        for c in consumers:
            c.cancel()