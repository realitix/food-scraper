#!/usr/bin/env python3

import asyncio
from pyppeteer import launch


async def main():
    browser = await launch(headless=False)
    page = await browser.newPage()

    # Login
    await page.goto('https://cronometer.com/login/')
    await page.type('#login_user_form input[type="email"]', 'realitix@gmail.com')
    await page.type('#login_user_form input[type="password"]', 'wawa8900')
    await page.click('#login-button')
    await page.waitForSelector('a[href="#foods"]')

    # Go to food nav
    await page.click('a[href="#foods"]')

    # Go to food search
    await page.waitForXPath("//div[text()='Search Foods']")
    link = await page.xpath("//div[contains(text(), 'Search Foods')]")
    await link[0].click()

    # Click on + Search Foods
    await page.waitForXPath("//button[text()='+ Search Foods']")
    link = await page.xpath("//button[text()='+ Search Foods']")
    await link[0].click()

    # Retrieve search bar
    await page.waitForSelector('img[src="https://cdn1.cronometer.com/pix/search_magnifier_v2.png"]')
    img_search = await page.querySelector('img[src="https://cdn1.cronometer.com/pix/search_magnifier_v2.png"]')
    search_bar = await page.evaluateHandle("el => el.nextElementSibling", img_search)

    # Retrieve searchbar button
    button_search_bar = await page.evaluateHandle("el => el.parentElement.nextElementSibling.nextElementSibling", search_bar)

    # Retrieve searchbar settings button
    search_bar_settings = await page.evaluateHandle("el => el.nextElementSibling", button_search_bar)

    # Click on settings
    await search_bar_settings.click()

    # Set source to nccdb
    select_selector = 'body > div.prettydialog > div > div > div.GL-TVABCPYB > div:nth-child(2) > table > tbody > tr > td:nth-child(2) > div > select'
    await page.waitForSelector(select_selector)
    await page.select(select_selector, 'NCCDB')

    # Write in search bar
    await search_bar.type("banana")

    # Click on button
    await button_search_bar.click()
    breakpoint()
    
    await browser.close()

asyncio.get_event_loop().run_until_complete(main())
