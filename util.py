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
import time

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

global_timestamp = 0


def get_timestamp():
    global global_timestamp
    if not global_timestamp:
        global_timestamp = int(time.time())
    return global_timestamp


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


def jsonify_nutrients(nutrients):
    result = {
        "aliment_name": nutrients['title'],
        "energy": nutrients['nutrition']['general'][0]['value'],
        "alcohol": nutrients['nutrition']['general'][2]['value'],
        "ash": nutrients['nutrition']['general'][3]['value'],
        "caffeine": nutrients['nutrition']['general'][5]['value'],
        "water": nutrients['nutrition']['general'][6]['value'],

        "carbs": nutrients['nutrition']['carbohydrates'][0]['value'],
        "fiber": nutrients['nutrition']['carbohydrates'][1]['value'],
        "starch": nutrients['nutrition']['carbohydrates'][2]['value'],
        "sugars": nutrients['nutrition']['carbohydrates'][3]['value'],
        "fructose": nutrients['nutrition']['carbohydrates'][4]['value'],
        "galactose": nutrients['nutrition']['carbohydrates'][5]['value'],
        "glucose": nutrients['nutrition']['carbohydrates'][6]['value'],
        "lactose": nutrients['nutrition']['carbohydrates'][7]['value'],
        "maltose": nutrients['nutrition']['carbohydrates'][8]['value'],
        "sucrose": nutrients['nutrition']['carbohydrates'][9]['value'],
        "sugar_added": nutrients['nutrition']['carbohydrates'][10]['value'],
        "sugar_alcohol": nutrients['nutrition']['carbohydrates'][11]['value'],

        "fat": nutrients['nutrition']['lipids'][0]['value'],
        "monounsaturated": nutrients['nutrition']['lipids'][1]['value'],
        "omega3": nutrients['nutrition']['lipids'][3]['value'],
        "omega6": nutrients['nutrition']['lipids'][4]['value'],
        "saturated": nutrients['nutrition']['lipids'][5]['value'],
        "trans_fats": nutrients['nutrition']['lipids'][6]['value'],
        "cholesterol": nutrients['nutrition']['lipids'][7]['value'],

        "protein": nutrients['nutrition']['proteins'][0]['value'],
        "alanine": nutrients['nutrition']['proteins'][1]['value'],
        "arginine": nutrients['nutrition']['proteins'][2]['value'],
        "aspartic_acid": nutrients['nutrition']['proteins'][3]['value'],
        "cystine": nutrients['nutrition']['proteins'][4]['value'],
        "glutamic_acid": nutrients['nutrition']['proteins'][5]['value'],
        "glycine": nutrients['nutrition']['proteins'][6]['value'],
        "histidine": nutrients['nutrition']['proteins'][7]['value'],
        "hydroxyproline": nutrients['nutrition']['proteins'][8]['value'],
        "isoleucine": nutrients['nutrition']['proteins'][9]['value'],
        "leucine": nutrients['nutrition']['proteins'][10]['value'],
        "lysine": nutrients['nutrition']['proteins'][11]['value'],
        "methionine": nutrients['nutrition']['proteins'][12]['value'],
        "phenylalanine": nutrients['nutrition']['proteins'][13]['value'],
        "proline": nutrients['nutrition']['proteins'][14]['value'],
        "serine": nutrients['nutrition']['proteins'][15]['value'],
        "threonine": nutrients['nutrition']['proteins'][16]['value'],
        "tryptophan": nutrients['nutrition']['proteins'][17]['value'],
        "tyrosine": nutrients['nutrition']['proteins'][18]['value'],
        "valine": nutrients['nutrition']['proteins'][19]['value'],

        "b1": nutrients['nutrition']['vitamins'][0]['value'],
        "b2": nutrients['nutrition']['vitamins'][1]['value'],
        "b3": nutrients['nutrition']['vitamins'][2]['value'],
        "b5": nutrients['nutrition']['vitamins'][3]['value'],
        "b6": nutrients['nutrition']['vitamins'][4]['value'],
        "b12": nutrients['nutrition']['vitamins'][5]['value'],
        "biotin": nutrients['nutrition']['vitamins'][6]['value'],
        "choline": nutrients['nutrition']['vitamins'][7]['value'],
        "folate": nutrients['nutrition']['vitamins'][8]['value'],
        "a": nutrients['nutrition']['vitamins'][9]['value'],
        "alpha_carotene": nutrients['nutrition']['vitamins'][10]['value'],
        "beta_carotene": nutrients['nutrition']['vitamins'][11]['value'],
        "beta_cryptoxanthin": nutrients['nutrition']['vitamins'][12]['value'],
        "lutein_zeaxanthin": nutrients['nutrition']['vitamins'][13]['value'],
        "lycopene": nutrients['nutrition']['vitamins'][14]['value'],
        "retinol": nutrients['nutrition']['vitamins'][15]['value'],
        "retinol_activity_equivalent": nutrients['nutrition']['vitamins'][16]['value'],
        "c": nutrients['nutrition']['vitamins'][17]['value'],
        "d": nutrients['nutrition']['vitamins'][18]['value'],
        "e": nutrients['nutrition']['vitamins'][19]['value'],
        "beta_tocopherol": nutrients['nutrition']['vitamins'][20]['value'],
        "delta_tocopherol": nutrients['nutrition']['vitamins'][21]['value'],
        "gamma_tocopherol": nutrients['nutrition']['vitamins'][22]['value'],
        "k": nutrients['nutrition']['vitamins'][23]['value'],

        "calcium": nutrients['nutrition']['minerals'][0]['value'],
        "chromium": nutrients['nutrition']['minerals'][1]['value'],
        "copper": nutrients['nutrition']['minerals'][2]['value'],
        "fluoride": nutrients['nutrition']['minerals'][3]['value'],
        "iodine": nutrients['nutrition']['minerals'][4]['value'],
        "iron": nutrients['nutrition']['minerals'][5]['value'],
        "magnesium": nutrients['nutrition']['minerals'][6]['value'],
        "manganese": nutrients['nutrition']['minerals'][7]['value'],
        "molybdenum": nutrients['nutrition']['minerals'][8]['value'],
        "phosphorus": nutrients['nutrition']['minerals'][9]['value'],
        "potassium": nutrients['nutrition']['minerals'][10]['value'],
        "selenium": nutrients['nutrition']['minerals'][11]['value'],
        "sodium": nutrients['nutrition']['minerals'][12]['value'],
        "zinc": nutrients['nutrition']['minerals'][13]['value'],
    }
    return json.dumps(json.loads(json.dumps(result), parse_float=lambda x: round(float(x), 3)), indent=4)