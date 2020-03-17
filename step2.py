from util import *


NON_EXISTENT_PATH = path.join(HERE, 'cache', 'step2', 'non-existent')

async def getRetrieve(page):
    result = {}
    def s(short_str):
        result = ""
        for short in short_str:
            if short == "f":
                result += ".firstElementChild"
            elif short == "p":
                result += ".parentElement"
            elif short == "n":
                result += ".nextElementSibling"
            else:
                raise Exception("Bad short string") 
        return "el => el"+result
    
    await page.waitFor(1000)

    container_selector = '#cronometerApp > div:nth-child(2) > div:nth-child(3) > div > div > table > tbody > tr:nth-child(2) > td > div > div:nth-child(4) > div > div > div.admin-food-editor-content-area'
    await page.waitForSelector(container_selector)
    container = await page.querySelector(container_selector)
    
    result['title'] = await page.evaluate("c => c.querySelector('div:nth-child(3) > div.admin-food-name').textContent", container)
    result['id'] = await page.evaluate("c => c.querySelector('div:nth-child(4) > div > div:nth-child(1)').textContent", container)
    languages = await container.querySelectorAll(".admin-nutrient-left > div:nth-child(1) > div > div > table > tbody > tr:nth-child(n)")
    rlang = []
    for l in languages:
        lang_name = await page.evaluate("el => el.firstElementChild.nextElementSibling.firstElementChild.textContent", l)
        lang_val = await page.evaluate("el => el.firstElementChild.nextElementSibling.nextElementSibling.nextElementSibling.textContent", l)
        rlang.append({'lang': lang_name, 'val': lang_val})
    result['name'] = rlang

    result['category'] = await page.evaluate("c => c.querySelector('.admin-nutrient-left > div:nth-child(2) > div > span > select').value", container)
    measures = await container.querySelectorAll('.admin-nutrient-left > div:nth-child(5) > div > table > tbody > tr > td > table > tbody > tr:nth-child(n+2)')
    rmeasures = []
    for m in measures:
        measure_name = await page.evaluate("el => el.firstElementChild.nextElementSibling.firstElementChild.textContent", m)
        measure_val = await page.evaluate("el => el.firstElementChild.nextElementSibling.nextElementSibling.firstElementChild.textContent", m)
        rmeasures.append({'name': measure_name, 'value': measure_val})
    result['measures'] = rmeasures

    # Set nutrients for 100g
    gram_input = await container.querySelector('div:nth-child(9) > div > div > div:nth-child(1) > input')
    gram_select = await container.querySelector('div:nth-child(9) > div > div > div:nth-child(1) > select')

    await gram_input.click({'clickCount': 3})
    await gram_input.type("");
    await gram_input.type("1000");
    await page.evaluate('''
        (element, values) => 
    {
        const options = Array.from(element.options);
        element.value = undefined;
        for (const option of options) {
            option.selected = values.includes(option.value);
            if (option.selected && !element.multiple)
                break;
        }
        element.dispatchEvent(new Event('input', { 'bubbles': true }));
        element.dispatchEvent(new Event('change', { 'bubbles': true }));
        return options.filter(option => option.selected).map(options => options.value)
    }
    ''', gram_select, ['g'])
    await page.waitFor(200)

    async def get_table_nutrients(table_element):
        nutrient_elems = await table_element.querySelectorAll('tbody > tr:nth-child(n+2)')
        results = []
        for e in nutrient_elems:
            nutrient_name = await page.evaluate('el => el.firstElementChild.firstElementChild.textContent', e)
            nutrient_value = await page.evaluate('el => el.firstElementChild.nextElementSibling.firstElementChild.textContent', e)
            nutrient_unit = await page.evaluate('el => el.firstElementChild.nextElementSibling.nextElementSibling.firstElementChild.textContent', e)
            r = dict()
            r['name'] = nutrient_name.strip()
            r['unit'] = nutrient_unit
            try:
                r['value'] = float(nutrient_value)/10
            except ValueError:
                r['value'] = 0.0

            results.append(r)
        return results

    # Get general nutrients
    tables = {
        'general'      : 'div.admin-nutrient-tables > div:nth-child(1) > div > table:nth-child(1) > tbody > tr > td > table',
        'carbohydrates': 'div.admin-nutrient-tables > div:nth-child(1) > div > table:nth-child(2) > tbody > tr > td > table',
        'lipids'       : 'div.admin-nutrient-tables > div:nth-child(1) > div > table:nth-child(3) > tbody > tr > td > table',
        'proteins'     : 'div.admin-nutrient-tables > div:nth-child(1) > div > table:nth-child(4) > tbody > tr > td > table',
        'vitamins'     : 'div.admin-nutrient-tables > div:nth-child(2) > div > table:nth-child(1) > tbody > tr > td > table',
        'minerals'     : 'div.admin-nutrient-tables > div:nth-child(2) > div > table:nth-child(2) > tbody > tr > td > table'
    }

    result['nutrition'] = {}
    for key, val in tables.items():
        t = await container.querySelector(val)
        r = await get_table_nutrients(t)
        result['nutrition'][key] = r
        
    return result


async def goToAlimentDetail(page, aliment_name):
    lines = await page.querySelectorAll('body > div.prettydialog > div > div > div > div > div > div > div > table > tbody > tr:nth-child(n+2)')
    results = {}
    for line in lines:
        line_val = await page.evaluate("el => el.firstElementChild.firstElementChild.textContent", line)
        results[line] = line_val

    min_dist = 999999
    final_result = None
    for k, v in results.items():
        d = Levenshtein.distance(v, aliment_name)
        if d < min_dist:
            final_result = k
            min_dist = d

    if not final_result:
        print(f"No result for aliment {aliment_name} in goToAlimentDetail")
        return False
    try:
        await final_result.click({'clickCount': 2})
    except:
        print(f"No result for aliment {aliment_name} in goToAlimentDetail")
        return False

    return True


async def consume_aliment_to_retrieve(queue, browser):
    def write_to_cache(aliment, result):
        a_cleaned = aliment.replace('/', '')
        with open(path.join(HERE, 'cache', 'step2', a_cleaned), "w") as f:
            json.dump(result, f)
    
    def write_non_non_existant(aliment):
        with open(NON_EXISTENT_PATH, 'a') as f:
            f.write(aliment)
            f.write('\n')
    
    page = await init_page(browser)
    await goToFoodSearch(page)
    while True:
        try:
            aliment = await queue.get()
            print(f"Retrieve aliment: {aliment}")
            await openSearchBox(page)

            await search(page, aliment)
            ok = await goToAlimentDetail(page, aliment)
            if ok:
                result = await getRetrieve(page)
                write_to_cache(aliment, result)
            else:
                write_non_non_existant(aliment)
            await page.waitFor(500)
        
        except asyncio.CancelledError:
            print("consumer STOP")
            await page.close()
        except Exception as e:
            print(f"Stacktrace for aliment {aliment}")
            traceback.print_exc()
        else:
            queue.task_done()

    await page.close()


async def get_nutrients(browser, aliment):
    page = await init_page(browser)
    await goToFoodSearch(page)
    await openSearchBox(page)
    await search(page, aliment)
    await goToAlimentDetail(page, aliment)
    result = await getRetrieve(page)
    await page.close()
    return result


def get_aliments_to_retrieve():
    aliments_src = listdir(path.join(HERE, 'cache', 'step1'))
    results = set()
    for a in aliments_src:
        with open(path.join(HERE, 'cache', 'step1', a), "r") as f:
            for l in f.readlines():
                results.add(l)
    
    # remove non existent aliment
    with open(NON_EXISTENT_PATH, 'r') as f:
        remove = set(f.readlines())

    results = results - remove

    return results


async def run(browser):
    aliments_in = [x.strip() for x in get_aliments_to_retrieve()]
    alims_in = set()
    cached_aliments = set(listdir(path.join(HERE, 'cache', 'step2')))
    for a in aliments_in:
        a_cleaned = a.replace('/', '')
        if a_cleaned not in cached_aliments:
            alims_in.add(a)
    
    print(f"Aliments left to retrieve: {len(alims_in)}")
    if len(alims_in) > 0:
        queue = asyncio.Queue(NB_PROCESS)
        producer = produce_aliment_to_search(queue, alims_in)
        consumers = [asyncio.create_task(consume_aliment_to_retrieve(queue, browser)) for _ in range(NB_PROCESS)]
        for completed in asyncio.as_completed([producer, *consumers]):
            await completed
            break

        await queue.join()
        for c in consumers:
            c.cancel()