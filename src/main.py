from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    ElementNotInteractableException
)

from datetime import datetime
import time
import sys
import re

# ---------------- CONFIG -----------------✅
BOOKING_URL = "https://recreation.utoronto.ca/booking"
TARGET_DATE = "Apr 25, 2026"
TARGET_SLOT = "3 - 3:55 PM"     # slot you want
MAX_REFRESH = 12
REFRESH_DELAY = 0.25

target_dt = None  # will hold datetime when booking opens

# ------------ HELPER FUNCTIONS ------------✅

def test_click(method_name, click_function):
    try:
        click_function()
        print(f"{method_name}: SUCCESS")
        # time.sleep(5)  # wait to see result of click
    except Exception as e:
        print(f"{method_name}: FAILED")
        print("Error type:", type(e).__name__)
        print("Error message:", e)
    print("-----------")

def select_date(driver, date_text, timeout=10):
    xpath = f"//button[@data-date-text='{date_text}' and not(contains(@style,'display: none'))]"

    try:
        # Wait only for presence (NOT clickable)
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located(
                (By.CLASS_NAME, "single-date-select-button")
            )
        )

        buttons = driver.find_elements(By.CLASS_NAME, "single-date-select-button")

        date_btn = None

        for btn in buttons:
            print(f"date button: {btn.get_attribute('data-date-text')}")
            print(f"Displayed: {btn.is_displayed()}, Enabled: {btn.is_enabled()}")

            if btn.get_attribute("data-date-text") == date_text and btn.is_displayed() and btn.is_enabled():
                date_btn = btn
                break

        if not date_btn:
            raise Exception("Target date button not found.")

        # Scroll into view (prevents overlap issues) & click
        driver.execute_script("arguments[0].scrollIntoView({block:'center', inline: 'center'});", date_btn)
        time.sleep(0.3)  # small delay to ensure scroll has settled
        test_click("Selenium Date Click", lambda: date_btn.click())
        # Confirm selection changed
        # WebDriverWait(driver, timeout).until(
        #     lambda d: d.find_element(
        #         By.XPATH, "//button[@aria-current='date']"
        #     ).get_attribute("data-date-text") == date_text
        # )
        return True

    except TimeoutException:
        print(f"Date '{date_text}' not selectable.")
        return False
    
def book_if_open(driver, slot_text, timeout=10):
    try:
        slot_xpath = (
            f"//div[contains(@class,'booking-slot-item') "
            f"and contains(., '{slot_text}')]"
        )

        # Wait for slot to appear
        slot = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, slot_xpath))
        )

    except TimeoutException:
        print("❌ Slot not found.")
        return False

    # Now slot exists. Handle inner failures separately.

    try:
        book_btn = slot.find_element(By.XPATH, ".//button")
    except NoSuchElementException:
        print("❌ Slot found but no button inside.")
        return False

    try:
        if book_btn.is_displayed() and book_btn.is_enabled():
            book_btn.click()
            print("✅ Slot is open and clicked.")
            return True
        else:
            print("❌ Button exists but not enabled.")
            return False

    except (ElementClickInterceptedException,
            ElementNotInteractableException,
            StaleElementReferenceException) as e:
        print(f"❌ Click failed: {type(e).__name__}")
        return False

# -------------------------------------------✅
options = Options()
service = Service()
driver = webdriver.Chrome(service=service, options=options)
driver.get(BOOKING_URL)

# wait for user to log in manually
input("✅ Log in manually, navigate to your court page, then press ENTER...")

# Ensure correct date selected before any detection
select_date(driver, TARGET_DATE, 10)
print("👀 Locating target slot...")

# -------- FIND THE SLOT CARD -------------✅
# Case 1: slot already open (Book button enabled)
if book_if_open(driver, TARGET_SLOT, timeout=2):
    print("AAAAAAA")
    time.sleep(15)  # wait to see result of click
    sys.exit(0)

else:
    print("HHHHHHHHHH")
    # Wait for booking grid to reload after date switch
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located(
            (By.CLASS_NAME, "booking-slot-item")
        )
    )
    print("222222222")
    slots = driver.find_elements(By.CLASS_NAME, "booking-slot-item")

    target_slot = None

    for s in slots:
        print(f"Slot found: {s.text[:30]}... Displayed: {s.is_displayed()}")
        if TARGET_SLOT in s.text and s.is_displayed():
            target_slot = s
            break

    if not target_slot:
        raise Exception("Target slot not found after date switch.")
    
    slot_text = target_slot.text
    print(f"Target slot text 111111: {slot_text}")
# --------------------------------------------------------------------------------
    if "Opens at" in slot_text:
        time_match = re.search(r"\d{1,2}:\d{2}\s*(AM|PM)", slot_text)
        time_str = time_match.group(0)
        target_dt = datetime.strptime(time_str, "%I:%M %p").replace(
            year=datetime.now().year,
            month=datetime.now().month,
            day=datetime.now().day
        )
        print(f"⏳ Booking opens at {target_dt.time()}")
    elif "No spots available" in slot_text or "UNAVAILABLE" in slot_text:
        print("🚫 Slot permanently unavailable.")
        sys.exit(0)
    else:
        raise RuntimeError("❌ Unexpected slot state.")

# -------- WAIT UNTIL BOOKING OPENS --------
if target_dt:
    print("⏳ Waiting for booking window...")
    while True:
        now = datetime.now()
        remaining = (target_dt - now).total_seconds()

        if remaining <= 0:
            break
        time.sleep(min(remaining, 0.1))
        print(f"current time: {now.time()}, waiting for: {target_dt.time()}", end="\r")

    print("🚀 Booking window opened — start polling.")

# -------- POLL + CLICK -------------------✅
for attempt in range(MAX_REFRESH):
    driver.refresh()
    select_date(driver, TARGET_DATE, timeout=5)

    try:
        if book_if_open(driver, TARGET_SLOT, timeout=3):
            print("🎾 Successfully booked.")
            time.sleep(15)  # wait to see result of click
            sys.exit(0)
    except TimeoutException:
        print(f"⏳ Attempt {attempt + 1}: still locked")


# ----------------------- VERSION 2 -----------------------
# 1. Define constants
# 2. Set up Selenium
# 3. Manually navigate to booking page
# 4. Locate target slot
# 5. IF slot if available:
#     - Click immediately
#     - Exit
# 6. ELSE:
#     - Extract "Opens at ..." time and parse it
#     - Wait until that time
#     - Enter polling loop:
#         - Refresh page
#         - Re-select correct date (important!)
#         - Check for enabled button
#         - If found, click and exit
#         - Else, wait and retry until max attempts reached
# ----------------------------------------------------------

# def select_date(driver, date_text):
#     # Wait for and click date selector button
#     date_button = WebDriverWait(driver, 10).until(
#         EC.element_to_be_clickable(
#             (By.XPATH, "//button[@data-target='#modalSingleDateSelector']")
#         )
#     )
#     driver.execute_script("arguments[0].click();", date_button)

#     # Wait for modal to be visible
#     WebDriverWait(driver, 5).until(
#         EC.visibility_of_element_located((By.ID, "modalSingleDateSelector"))
#     )

#     # Wait for correct date button to be clickable
#     date_option = WebDriverWait(driver, 5).until(
#         EC.element_to_be_clickable(
#             (By.XPATH, f"//button[@data-date-text='{date_text}']")
#         )
#     )

#     driver.execute_script("arguments[0].click();", date_option)

#     time.sleep(0.3)