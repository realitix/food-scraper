import xmltodict
import json
from os import path
from os import listdir
import asyncio
from pyppeteer import launch
from pyppeteer.errors import TimeoutError, NetworkError

HERE = path.dirname(path.abspath(__file__))

NB_PROCESS = 1
WINDOW = True

URL_HOME = 'https://cronometer.com'
URL_LOGIN = 'https://cronometer.com/login/'
LOGIN_MAIL = '#login_user_form input[type="email"]'
LOGIN_PASS = '#login_user_form input[type="password"]'
LOGIN_BTN = '#login-button'
FOOD_NAV = 'a[href="#foods"]'
CLOSE_GOLD = 'body > div:nth-child(15) > div > div > div.titlebar > div.titlebar-cancelbox'
FOOD_SEARCH = "//div[text()='Search Foods']"
FOOD_SRC_BTN = "//button[text()='+ Search Foods']"
SRC_IMG = "img[src='https://cdn1.cronometer.com/pix/search_magnifier_v2.png']"
SRC_TABLE_ALL_RESULT = 'body > div.prettydialog > div > div > div.GL-TVABCNYB > div.GL-TVABCE-B > div > div > div > table > tbody > tr:nth-child(n)'
SRC_TABLE_COL_NAME = 'td:nth-child(1) > div'
SRC_BTN_VIEW_RESULT = 'body > div.prettydialog > div > div > table > tbody > tr > td:nth-child(2) > button'
SRC_LOADING_IMG = 'body > div.prettydialog > div > div > div.GL-TVABCNYB > div:nth-child(1) > div > img.GL-TVABCK-B'
SRC_GOTO_ALIMENT = 'body > div.prettydialog > div > div > table > tbody > tr > td:nth-child(2) > button'

# Food detail
GLOBAL_GOOD_DETAIL = '.admin-food-editor-content-area'



def patch_pyppeteer():
    from typing import Any
    from pyppeteer import connection, launcher
    import websockets.client

    class PatchedConnection(connection.Connection):  # type: ignore
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            # the _ws argument is not yet connected, can simply be replaced with another
            # with better defaults.
            self._ws = websockets.client.connect(
                self._url,
                loop=self._loop,
                # the following parameters are all passed to WebSocketCommonProtocol
                # which markes all three as Optional, but connect() doesn't, hence the liberal
                # use of type: ignore on these lines.
                # fixed upstream but not yet released, see aaugustin/websockets#93ad88
                max_size=None,  # type: ignore
                ping_interval=None,  # type: ignore
                ping_timeout=None,  # type: ignore
            )

    connection.Connection = PatchedConnection
    # also imported as a  global in pyppeteer.launcher
    launcher.Connection = PatchedConnection


async def login(page):
    await page.goto(URL_LOGIN)
    await page.type(LOGIN_MAIL, 'realitix@gmail.com')
    await page.type(LOGIN_PASS, 'wawa8900')
    await page.click(LOGIN_BTN)


async def goToFoodNav(page):
    await page.waitForSelector(FOOD_NAV, {'timeout': 60000})
    await page.click(FOOD_NAV)


async def goToFoodSearch(page):
    await page.waitForXPath(FOOD_SEARCH)
    link = await page.xpath(FOOD_SEARCH)
    await link[0].click()


async def openSearchBox(page):
    await page.waitForXPath(FOOD_SRC_BTN)
    link = await page.xpath(FOOD_SRC_BTN)
    await link[0].click()


async def search(page, text_search):
    await page.waitFor(1000)
    await page.waitForSelector(SRC_IMG)
    img_search_bar = await page.querySelector(SRC_IMG)
    search_bar = await page.evaluateHandle("el => el.nextElementSibling", img_search_bar)
    img_loading = await page.evaluateHandle("el => el.parentElement.nextElementSibling", search_bar)
    button = await page.evaluateHandle("el => el.nextElementSibling", img_loading)
    settings_button = await page.evaluateHandle("el => el.nextElementSibling", button)

    async def p(node):
        t = await node.getProperty('nodeName')
        tt = await t.jsonValue()
        print(tt)


    # Set source to nccdb
    await settings_button.click()
    select = await page.evaluateHandle('''
        el => el
            .parentElement
            .parentElement
            .nextElementSibling
            .firstElementChild
            .firstElementChild
            .firstElementChild
            .firstElementChild
            .nextElementSibling
            .firstElementChild
            .firstElementChild
            ''', settings_button)

    await page.evaluate('''
    (element, values) => {
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
    ''', select, ['NCCDB'])
    
    # Clean input
    await search_bar.click({'clickCount': 3})
    await search_bar.type("");

    # Start search
    await search_bar.type(text_search)
    await button.click()

    # Wait
    await page.waitFor(2000)
    await page.waitForFunction('el => el.style.visibility == "hidden"', None, img_loading)
    

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


async def viewResult(page, result):
    selector = "//div[text()='"+result+"']"
    elem = await page.xpath(selector)
    btn = await page.querySelector(SRC_BTN_VIEW_RESULT)
    try:
        await elem[0].click()
    except IndexError:
        print("Can't find result "+result)
        breakpoint()
        raise
    await btn.click()


async def removeGold(page):
    try:
        await page.waitForSelector(CLOSE_GOLD, {"timeout": 500})
        print("Close GOLD")
        close_button = await page.querySelector(CLOSE_GOLD)
        await close_button.click()
    except TimeoutError:
        pass


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


async def produce_aliment_to_search(queue, aliments):
    for a in aliments:
        await queue.put(a.strip())
    await queue.put(None)


async def consume_aliment_to_search(queue):
    def write_to_cache(aliment, results):
        with open(path.join(HERE, 'cache', 'step1', aliment), "w") as f:
            for r in results:
                f.write(r)
                f.write('\n')

    browser, page = await init_page()
    try:
        await goToFoodSearch(page)
        await openSearchBox(page)

        while True:
            aliment = await queue.get()
            if aliment is None:
                break

            print(f"Search aliment: {aliment}")

            await search(page, aliment)
            all_results = await getResults(page)
            write_to_cache(aliment, all_results)
            await page.waitFor(500)
            queue.task_done()
    except Exception as e:
        print(e)

    await browser.close()


async def init_page():
    params = {'headless': False, 'args': ["--start-maximized"]} if WINDOW else {}
    browser = await launch(**params)
    page = await browser.newPage()

    if WINDOW:
        await page.setViewport({'width':0, 'height':0})    
    
    await login(page)
    await goToFoodNav(page)
    return browser, page


def find_max_aliments(aliments_in):
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
        loop = asyncio.get_event_loop()
        queue = asyncio.Queue(loop=loop)
        producer = produce_aliment_to_search(queue, stills_alim)
        consumers = [consume_aliment_to_search(queue) for _ in range(NB_PROCESS)]
        loop.run_until_complete(asyncio.gather(producer, *consumers))
        loop.close()
    

def get_aliments_to_retrieve():
    aliments_src = listdir(path.join(HERE, 'cache', 'step1'))
    results = set()
    for a in aliments_src:
        with open(path.join(HERE, 'cache', 'step1', a), "r") as f:
            for l in f.readlines():
                results.add(l)

    print(f"{len(results)} aliments to retrieve")
    return results


async def goToAlimentDetail(page, aliment_name):
    if "'" in aliment_name:
        search_name = f'"{aliment_name}"'
    else:
        search_name = f"'{aliment_name}'"

    xpath_name = f"//div[text()={search_name}]"
    await page.waitForXPath(xpath_name)
    link = await page.xpath(xpath_name)
    await link[0].click({'clickCount': 2})


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
    await page.waitForSelector(GLOBAL_GOOD_DETAIL)
    container = await page.querySelector(GLOBAL_GOOD_DETAIL)
    title = await page.evaluateHandle(s("fnnfn"), container)
    nutrient_left = await page.querySelector(".admin-nutrient-left")
    languages = await page.querySelectorAll(".admin-nutrient-left > div:nth-child(1) > div > div > table > tbody > tr:nth-child(n)")
    rlang = []
    for l in languages:
        lang_name = await page.evaluate("el => el.firstElementChild.nextElementSibling.firstElementChild.textContent", l)
        lang_val = await page.evaluate("el => el.firstElementChild.nextElementSibling.nextElementSibling.nextElementSibling.textContent", l)
        rlang.append({'lang': lang_name, 'val': lang_val})
    result['name'] = rlang

    category = await page.querySelector('.admin-nutrient-left > div:nth-child(2) > div > span > select')
    result['category'] = await page.evaluate('el => el.textContent', category)
    print(result['category'])




async def consume_aliment_to_retrieve(queue):
    def write_to_cache(aliment, result):
        a_cleaned = aliment.replace('/', '')
        with open(path.join(HERE, 'cache', 'step2', a_cleaned), "w") as f:
            json.dump(result, f)
    
    browser, page = await init_page()
    try:
        await goToFoodSearch(page)
        while True:
            await openSearchBox(page)
            
            aliment = await queue.get()
            if aliment is None:
                break

            print(f"Retrieve aliment: {aliment}")

            await search(page, aliment)
            await goToAlimentDetail(page, aliment)
            result = await getRetrieve(page)
            write_to_cache(aliment, result)
            await page.waitFor(500)
            queue.task_done()
    except Exception as e:
        print(e)

    await browser.close()


def retrieve(aliments_in):
    alims_in = set()
    cached_aliments = set(listdir(path.join(HERE, 'cache', 'step2')))
    for a in aliments_in:
        a_cleaned = a.replace('/', '')
        if a_cleaned not in cached_aliments:
            alims_in.add(a)
    
    print(f"Aliments left to retrieve: {len(alims_in)}")
    if len(alims_in) > 0:
        loop = asyncio.get_event_loop()
        queue = asyncio.Queue(loop=loop)
        producer = produce_aliment_to_search(queue, alims_in)
        consumers = [consume_aliment_to_retrieve(queue) for _ in range(NB_PROCESS)]
        loop.run_until_complete(asyncio.gather(producer, *consumers))
        loop.close()