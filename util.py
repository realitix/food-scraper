import xmltodict
from os import path
from os import listdir
import asyncio
from pyppeteer import launch
from pyppeteer.errors import TimeoutError, NetworkError

HERE = path.dirname(path.abspath(__file__))

NB_PROCESS = 10

URL_HOME = 'https://cronometer.com'
URL_LOGIN = 'https://cronometer.com/login/'
LOGIN_MAIL = '#login_user_form input[type="email"]'
LOGIN_PASS = '#login_user_form input[type="password"]'
LOGIN_BTN = '#login-button'
FOOD_NAV = 'a[href="#foods"]'
CLOSE_GOLD = 'body > div:nth-child(15) > div > div > div.titlebar > div.titlebar-cancelbox'
FOOD_SEARCH = "//div[text()='Search Foods']"
FOOD_SRC_BTN = "//button[text()='+ Search Foods']"
SRC_INPUT = "body > div.prettydialog > div > div > div.GL-TVABCNYB > div:nth-child(1) > div > div > input"
SRC_BTN = 'body > div.prettydialog > div > div > div.GL-TVABCNYB > div:nth-child(1) > div > button'
SRC_SETTING_BTN = "body > div.prettydialog > div > div > div.GL-TVABCNYB > div:nth-child(1) > div > img.GL-TVABCKYB"
SRC_SETTING_SELECT = 'body > div.prettydialog > div > div > div.GL-TVABCNYB > div:nth-child(2) > table > tbody > tr > td:nth-child(2) > div > select'
SRC_TABLE_RESULT = 'body > div.prettydialog > div > div > div.GL-TVABCNYB > div.GL-TVABCE-B > div > div > div > table > tbody'
SRC_TABLE_FIRST_RESULT = 'body > div.prettydialog > div > div > div.GL-TVABCNYB > div.GL-TVABCE-B > div > div > div > table > tbody > tr:nth-child(2)'
SRC_TABLE_ALL_RESULT = 'body > div.prettydialog > div > div > div.GL-TVABCNYB > div.GL-TVABCE-B > div > div > div > table > tbody > tr:nth-child(n)'
SRC_TABLE_COL_NAME = 'td:nth-child(1) > div'
SRC_BTN_VIEW_RESULT = 'body > div.prettydialog > div > div > table > tbody > tr > td:nth-child(2) > button'
SRC_LOADING_IMG = 'body > div.prettydialog > div > div > div.GL-TVABCNYB > div:nth-child(1) > div > img.GL-TVABCK-B'


def _patch_pyppeteer():
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
    await page.waitForSelector(SRC_INPUT)
    search_bar = await page.querySelector(SRC_INPUT)
    button = await page.querySelector(SRC_BTN)

    # Set source to nccdb
    settings_button = await page.querySelector(SRC_SETTING_BTN)
    await settings_button.click()
    await page.waitForSelector(SRC_SETTING_SELECT)
    await page.select(SRC_SETTING_SELECT, 'NCCDB')
    
    # Clean input
    await search_bar.click({'clickCount': 3})
    await search_bar.type("");

    # Start search
    await search_bar.type(text_search)
    await page.waitFor(1000)
    await button.click()


async def waitForSearchLoading(page):
    await page.waitFor(1000)
    await page.waitForSelector(SRC_LOADING_IMG)
    await page.waitForFunction('document.querySelector("'+SRC_LOADING_IMG+'").style.visibility == "hidden"')
    

async def getResults(page):
    #await page.waitForSelector(SRC_TABLE_FIRST_RESULT)
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


async def run_chrome():
    util._patch_pyppeteer()
    with open("alim_list_in.txt") as f:
        alim_flat_in = f.readlines()

    with open("alim_list_in.cache") as f:
        alim_flat_in_cache = f.readlines()

    browser = await launch(headless=False, args=["--start-maximized"])
    page = await browser.newPage()
    await page.setViewport({'width':0, 'height':0});

    await login(page)
    try:
        await goToFoodNav(page)
        await goToFoodSearch(page)
        await openSearchBox(page)

        for a in alim_flat_in:
            if a in alim_flat_in_cache:
                continue
            
            try:
                await search(page, a)
                await waitForSearchLoading(page)
                all_results = await getResults(page)
                await write(all_results, a)
                await page.waitFor(500)
            except Exception as e:
                print("Error for aliment "+a)
                print(e)
                continue
        #await viewResult(page, all_results[0])
    except TimeoutError:
        # Probably the gold page lock
        print("TimeOut Error")
        raise
        #await removeGold(page)
        #raise
    except NetworkError:
        # Probably the gold page lock
        print("Network Error")
        raise
        #await removeGold(page)
        #raise

    breakpoint()
    
    await browser.close()


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
        await queue.put(a)
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
            await waitForSearchLoading(page)
            all_results = await getResults(page)
            write_to_cache(aliment, all_results)
            await page.waitFor(500)
            queue.task_done()
    except Exception as e:
        print(e)

    await browser.close()


async def init_page():
    #browser = await launch(headless=False, args=["--start-maximized"])
    browser = await launch()
    page = await browser.newPage()
    #await page.setViewport({'width':0, 'height':0})
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

    # Start the process
    _patch_pyppeteer()
    
    if len(stills_alim) > 0:
        loop = asyncio.get_event_loop()
        queue = asyncio.Queue(loop=loop)
        producer = produce_aliment_to_search(queue, stills_alim)
        consumers = [consume_aliment_to_search(queue) for _ in range(NB_PROCESS)]
        loop.run_until_complete(asyncio.gather(producer, *consumers))
        loop.close()



async def test():
    _patch_pyppeteer()
    browser = await launch(headless=False, args=["--start-maximized"])
    page = await browser.newPage()
    await page.setViewport({'width':0, 'height':0})
    await login(page)
    await goToFoodNav(page)

    # Check new page if connected
    page2 = await browser.newPage()
    await page2.setViewport({'width':0, 'height':0})
    await page2.goto(URL_HOME)
    breakpoint()
