from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import random
import time

def calculate_bezier_point(p0, p1, p2, p3, t):
    """Calculates a coordinate point along a Cubic Bézier curve."""
    x = (1-t)**3 * p0[0] + 3*(1-t)**2 * t * p1[0] + 3*(1-t) * t**2 * p2[0] + t**3 * p3[0]
    y = (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p1[1] + 3*(1-t) * t**2 * p2[1] + t**3 * p3[1]
    return int(x), int(y)

def human_mouse_move(page, start_x, start_y, end_x, end_y, steps=25):
    """Moves the mouse over a randomized curve path to look human-like."""
    control_x1 = start_x + (end_x - start_x) * random.uniform(0.1, 0.4) + random.randint(-50, 50)
    control_y1 = start_y + (end_y - start_y) * random.uniform(0.1, 0.4) + random.randint(-50, 50)
    control_x2 = start_x + (end_x - start_x) * random.uniform(0.6, 0.9) + random.randint(-50, 50)
    control_y2 = start_y + (end_y - start_y) * random.uniform(0.6, 0.9) + random.randint(-50, 50)
    
    p0 = (start_x, start_y)
    p1 = (control_x1, control_y1)
    p2 = (control_x2, control_y2)
    p3 = (end_x, end_y)
    
    for i in range(steps + 1):
        t = i / steps
        t_eased = t * t * (3 - 2 * t) 
        x, y = calculate_bezier_point(p0, p1, p2, p3, t_eased)
        page.mouse.move(x, y)
        time.sleep(random.uniform(0.008, 0.02))

# def main():
    search_term = "Swanavon Dental Clinic" 
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        )
        
        context = browser.new_context(
            viewport=None,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("Opening Brownbook Canada...")
        page.goto("https://www.brownbook.net/country-selector/ca", wait_until="networkidle")

        # 1. Trigger search layout
        print("Activating search input box...")
        page.locator('input[placeholder="Business type or name"]').first.click()
        page.wait_for_selector('div[role="dialog"], form', state="visible", timeout=10000)
        page.wait_for_timeout(1000)

        # 2. Type business query
        print(f"Typing business name: '{search_term}'...")
        popup_input = page.locator('div[role="dialog"] input[placeholder="Business type or name"]').first
        popup_input.click()
        
        for char in search_term:
            popup_input.type(char)
            time.sleep(random.uniform(0.05, 0.15))
            
        page.wait_for_timeout(500)
        
        # 3. Submit
        print("Submitting query...")
        popup_input.press("Enter")
        
        # 4. Handle Captcha Interface
        print("Checking page result status...")
        page.wait_for_timeout(5000)
        
        captcha_element = page.locator("iframe[src*='recaptcha/api2/anchor']").first
        
        if captcha_element.count() > 0:
            print("\n[+] reCAPTCHA widget found on screen.")
            box_bounding_box = captcha_element.bounding_box()
            
            if box_bounding_box:
                target_x = box_bounding_box["x"] + 30 + random.randint(-3, 3)
                target_y = box_bounding_box["y"] + 35 + random.randint(-3, 3)
                
                start_x = random.randint(10, 150)
                start_y = random.randint(10, 150)
                page.mouse.move(start_x, start_y)
                page.wait_for_timeout(400)
                
                print(f"[+] Moving mouse smoothly to target coordinate: ({target_x}, {target_y})...")
                human_mouse_move(page, start_x, start_y, target_x, target_y, steps=30)
                page.wait_for_timeout(random.randint(200, 500))
                
                page.mouse.down()
                page.wait_for_timeout(random.randint(60, 120))
                page.mouse.up()
                print("[+] Mouse sequence finished.")
                
            page.wait_for_timeout(4000)

        # 5. Evaluate challenge and load results listing page
        print("[+] Evaluating checkbox challenge success status...")
        puzzle_iframe = page.locator("iframe[src*='recaptcha/api2/bframe']").first
        
        if puzzle_iframe.count() > 0 and puzzle_iframe.is_visible():
            print("[!] Deadlock detected: Google blocked the session with an image selection puzzle grid!")
            browser.close()
            return

        print("[+] Captcha challenge passed or absent. Verifying listing tables...")
        results_selector = "a[href*='/business/']"
        try:
            page.wait_for_selector(results_selector, timeout=15000)
            print("[+] Listing page verified successfully!")
        except Exception:
            print("[-] Profile list rows failed to load automatically.")
            browser.close()
            return

        # -------------------------------------------------------------
        # 6. EXTRACT SEARCH RESULTS AND FILTER FOR THE EXACT MATCH
        # -------------------------------------------------------------
        soup_results = BeautifulSoup(page.content(), "html.parser")
        matched_url = None

        print("\nReviewing search result cards for target term...")
        # Search systematically across all anchor hyperlinks linking to business nodes
        for a in soup_results.find_all("a", href=True):
            href = a["href"]
            if "/business/" in href:
                link_text = a.get_text().strip()
                full_url = href if href.startswith("http") else f"https://www.brownbook.net{href}"
                
                # Check if our exact search target phrase lives within the result link text
                if search_term.lower() in link_text.lower():
                    print(f"[+] Found Match in listing text: '{link_text}'")
                    matched_url = full_url
                    break

        # Fallback Strategy: If text contents were wrapped in internal spans, use the first available result
        if not matched_url:
            print("[!] Exact text block link match missed. Falling back to the first available business link item...")
            for a in soup_results.find_all("a", href=True):
                if "/business/" in a["href"]:
                    matched_url = a["href"] if a["href"].startswith("http") else f"https://www.brownbook.net{a['href']}"
                    break

        if not matched_url:
            print("[-] No business profile endpoints were found on the search result index.")
            browser.close()
            return

        # -------------------------------------------------------------
        # 7. NAVIGATE TO MATCHED TARGET AND EXTRACT BUSINESS DATA (NAP)
        # -------------------------------------------------------------
        print(f"\nNavigating directly to profile page: {matched_url}")
        page.goto(matched_url, wait_until="networkidle")
        page.wait_for_timeout(1500)
        
        profile_soup = BeautifulSoup(page.content(), "html.parser")
        
        # Name Extraction via Microdata Tags
        name_header = profile_soup.find(itemprop="name") or profile_soup.find("h1")
        name = name_header.text.strip() if name_header else "N/A"

        # Address Extraction
        address_div = profile_soup.find(itemprop="address") or profile_soup.find(class_="address")
        address = address_div.get_text(separator=" ").strip() if address_div else "N/A"

        # Phone and Web Links Extraction
        phone = "N/A"
        external_links = []
        all_anchors = profile_soup.find_all("a", href=True)
        
        for anchor in all_anchors:
            href = anchor["href"]
            if "tel:" in href:
                phone = href.replace("tel:", "").strip()
            elif "mailto:" in href:
                email = href.replace("mailto:", "").strip()
                external_links.append(f"Email: {email}")
            elif any(domain in href for domain in ["http", "www", ".ca", ".com", "facebook", "instagram"]):
                if "brownbook.net" not in href and href not in external_links:
                    external_links.append(href)

        # Cleanup formatting items
        if phone != "N/A" and phone in address:
            address = address.split(phone)[0].strip()
        address = " ".join(address.split())

        print("\n================ SCRAPED PROFILE DATA ================")
        print(f"Name:    {name}")
        print(f"Address: {address}")
        print(f"Phone:   {phone}")
        print("Associated Resource Links:")
        for link in external_links:
            print(f"  - {link}")
        print("======================================================")

        browser.close()

# if __name__ == "__main__":
#     main()