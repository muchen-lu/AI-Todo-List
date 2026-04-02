import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://cooc.tp.edu.tw/oauth2/oauth/authorize?client_id=2gMSkBmGUSJVkwCrZz2fnMNtMj2Dfasc&response_type=code&redirect_uri=https%3A//ono.tp.edu.tw/login&state=L3VzZXIvaW5kZXg=&scope=User.Info,User.Role,User.RoleDetail,User.IDNumber,User.SSORole,User.EMail#/")
    page.get_by_text("臺北市校園單一身分驗證入口").click()
    page.get_by_role("textbox", name="帳號").click()
    page.get_by_role("textbox", name="帳號").fill("")
    page.get_by_role("textbox", name="密碼").click()
    page.get_by_role("textbox", name="密碼").fill("")
    page.get_by_role("button", name="登入", exact=True).click()
    page.goto("https://ono.tp.edu.tw/user/index#/")
    

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
