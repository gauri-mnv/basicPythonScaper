from playwright.sync_api import sync_playwright
from urllib.request import urlretrieve

pw = sync_playwright().start()

browser = pw.firefox.launch(
    headless=False
    #slow_mo=2000
    )

page = browser.new_page()

page.goto("https://arxiv.org/search")
page.get_by_placeholder("Search term...").fill("neural network")

page.get_by_role("button").get_by_text("Search").nth(1).click()

# wait until network requests are finished
page.wait_for_load_state("networkidle")

links = page.locator("xpath=//a[contains(@href, 'arxiv.org/pdf')]").all()

for link in links:
  #  print(link.get_attribute("href"))
  url = link.get_attribute("href")
  urlretrieve(url, "data/"+url[-5:]+".pdf")


print("Total links:", len(links))
# print(page.content())
print(page.title())

page.screenshot(path="ss.png")

browser.close()