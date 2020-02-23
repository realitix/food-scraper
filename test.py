#!/usr/bin/env python3

import asyncio
from pyppeteer import launch
from pyppeteer.errors import TimeoutError


URL = 'https://cronometer.com/login/'
LOGIN_MAIL = '#login_user_form input[type="email"]'
LOGIN_PASS = '#login_user_form input[type="password"]'
LOGIN_BTN = '#login-button'
FOOD_NAV = 'a[href="#foods"]'
CLOSE_GOLD = 'body > div:nth-child(15) > div > div > div.titlebar > div.titlebar-cancelbox'
FOOD_SEARCH = "//div[text()='Search Foods']"
FOOD_SRC_BTN = "//button[text()='+ Search Foods']"
SRC_INPUT = "body > div.prettydialog > div > div > div.GL-TVABCPYB > div:nth-child(1) > div > div > input"
SRC_BTN = 'body > div.prettydialog > div > div > div.GL-TVABCPYB > div:nth-child(1) > div > button'
SRC_SETTING_BTN = "body > div.prettydialog > div > div > div.GL-TVABCPYB > div:nth-child(1) > div > img.GL-TVABCMYB"
SRC_SETTING_SELECT = 'body > div.prettydialog > div > div > div.GL-TVABCPYB > div:nth-child(2) > table > tbody > tr > td:nth-child(2) > div > select'
SRC_TABLE_RESULT = 'body > div.prettydialog > div > div > div.GL-TVABCPYB > div.GL-TVABCE-B > div > div > div > table > tbody'
SRC_TABLE_FIRST_RESULT = 'body > div.prettydialog > div > div > div.GL-TVABCPYB > div.GL-TVABCE-B > div > div > div > table > tbody > tr:nth-child(2)'
SRC_TABLE_ALL_RESULT = 'body > div.prettydialog > div > div > div.GL-TVABCPYB > div.GL-TVABCE-B > div > div > div > table > tbody > tr:nth-child(n+1)'
SRC_TABLE_COL_NAME = 'td:nth-child(1) > div'
SRC_BTN_VIEW_RESULT = 'body > div.prettydialog > div > div > table > tbody > tr > td:nth-child(2) > button'


async def login(page):
    await page.goto(URL)
    await page.type(LOGIN_MAIL, 'realitix@gmail.com')
    await page.type(LOGIN_PASS, 'wawa8900')
    await page.click(LOGIN_BTN)


async def goToFoodNav(page):
    await page.waitForSelector(FOOD_NAV)
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
    await page.waitForSelector(SRC_INPUT)
    search_bar = await page.querySelector(SRC_INPUT)
    button = await page.querySelector(SRC_BTN)

    # Set source to nccdb
    settings_button = await page.querySelector(SRC_SETTING_BTN)
    await settings_button.click()
    await page.waitForSelector(SRC_SETTING_SELECT)
    await page.select(SRC_SETTING_SELECT, 'NCCDB')

    # Start search
    await search_bar.type(text_search)
    await button.click()


async def getResults(page):
    await page.waitForSelector(SRC_TABLE_FIRST_RESULT)
    elements = await page.querySelectorAll(SRC_TABLE_ALL_RESULT)
    all_names = []
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
    await elem[0].click()
    await btn.click()


async def checkGold(page):
    try:
        await page.waitForSelector(CLOSE_GOLD, {"timeout": 500})
        print("Close GOLD")
        close_button = await page.querySelector(CLOSE_GOLD)
        await close_button.click()
    except TimeoutError:
        pass


async def main():
    browser = await launch(headless=False, args=["--start-maximized"])
    page = await browser.newPage()
    await page.setViewport({'width':0, 'height':0});

    await login(page)
    await checkGold(page)
    await goToFoodNav(page)
    await checkGold(page)
    await goToFoodSearch(page)
    await checkGold(page)
    await openSearchBox(page)
    await checkGold(page)
    await search(page, "banana")
    await checkGold(page)
    all_results = await getResults(page)
    await checkGold(page)
    await viewResult(page, all_results[0])

    breakpoint()
    
    await browser.close()

asyncio.get_event_loop().run_until_complete(main())
