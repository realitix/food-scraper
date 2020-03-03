import xmltodict
import traceback
import json
from os import path
from os import listdir
import signal, psutil, os
import asyncio
from pyppeteer import launch
from pyppeteer.errors import TimeoutError, NetworkError
import Levenshtein

HERE = path.dirname(path.abspath(__file__))

NB_PROCESS = 5
WINDOW = False

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
    try:
        await link[0].click()
    except:
        print("Can't open SearchBox, retrying...")
        await openSearchBox(page)


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


async def removeGold(page):
    try:
        await page.waitForSelector(CLOSE_GOLD, {"timeout": 500})
        print("Close GOLD")
        close_button = await page.querySelector(CLOSE_GOLD)
        await close_button.click()
    except TimeoutError:
        pass


async def produce_aliment_to_search(queue, aliments):
    for a in aliments:
        await queue.put(a.strip())


async def init_browser():
    params = {'headless': False, 'args': ["--start-maximized"]} if WINDOW else {}
    browser = await launch(**params)
    page = await browser.newPage() 
    
    await login(page)
    await goToFoodNav(page)
    await page.close()
    return browser


async def init_page(browser):
    page = await browser.newPage()
    if WINDOW:
        await page.setViewport({'width':0, 'height':0})
    await page.goto(URL_HOME)  
    await goToFoodNav(page)
    return page