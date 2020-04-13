import bs4
from bs4 import NavigableString

from selenium import webdriver

import sys
import time
import os
import traceback
import logging
import tempfile
import re

from selenium.common.exceptions import NoSuchElementException

import pr_settings
import gmail

logging.basicConfig(format='%(asctime)s %(levelname)s : %(message)s', level=logging.INFO)
slot_container_with_date_regex = re.compile('^slot-container-(\d{4}-\d{2}-\d{2})$')
not_available_text = "No doorstep delivery windows are available".lower()


class HeartBeat:
    def __init__(self, freq_in_secs):
        self.freq_in_sec = freq_in_secs
        self.starting = time.time()

    def check(self):
        elapsed = time.time() - self.starting
        logging.info('elapsed sec : ' + str(elapsed))
        if elapsed > self.freq_in_sec:
            os.system('say "Program still alive"')
            self.starting = time.time()


class Slot:
    def __init__(self, dateStr, slots_open):
        self.dateStr = dateStr
        self.slotsOpen = slots_open

    def __str__(self):
        return "Slot[" + self.dateStr + (" HAS" if self.slotsOpen else " has NO") \
               + " open slots]"


def find_slot_from_slot_container_base(soup):
    """
    :param bs: beautifulsoup object
    :return:
    """
    slot_container_root = soup.find(id="slot-container-root")
    slots = []
    for slot in slot_container_root.findAll('div', id=slot_container_with_date_regex):
        dateStr = slot_container_with_date_regex.match(slot['id']).group(1)
        unattended_container = slot.find('div', id="slot-container-UNATTENDED")
        text = unattended_container.findAll(end_node)[0].text
        logging.debug("Found text : " + text)
        slotsOpen = False
        if (text is not None and text.lower().find(not_available_text) >= 0):
            slotsOpen = False
        else:
            slotsOpen = True
        slots.append(Slot(dateStr, slotsOpen))
    return slots


def alert(open_slots):
    slots_str = "slots : " + str([str(s) for s in open_slots])
    logging.info('SLOTS OPEN!')
    os.system('say "Slots for delivery opened!"')
    send_gmail(slots_str)
    logging.info('email sent')
    time.sleep(1400)


def saveToFile(folder, text):
    f = open(folder + next(tempfile._get_candidate_names())+'.html', "a")
    f.write(text)
    f.close()


def send_gmail(body_text):
    service = gmail.build_service()
    # Call the Gmail API
    msg = gmail.create_message(pr_settings.gmail_from, pr_settings.gmail_to, pr_settings.gmail_subject,
                               pr_settings.gmail_body+" "+body_text)
    gmail.send_message(service, 'me', msg)


def check_slots_algo1(soup):
    """
    :param soup: beautiful soup object representing the whole html
    :return: True if has open slots. False otherwise.
    """
    no_open_slots = True
    try:
        slots = find_slot_from_slot_container_base(soup)
        logging.info("slots : " + str([str(s) for s in slots]))
        open_slots = [sl for sl in slots if sl.slotsOpen]
        if len(open_slots) == 0:
            return False
        else:
            saveToFile(pr_settings.html_file_temp_folder, str(soup))
            alert(open_slots)
            return True
    except NoSuchElementException as e:
        traceback.print_exc(file=sys.stdout)


def end_node(tag):
    """
    Args:
      tag: html element.

    Returns: True if tag is a span and contains text and no other tags inside.
    """
    if tag.name not in ["span"]:
        return False
    if isinstance(tag, NavigableString):  # if str return
        return False
    if not tag.text:  # if no text return false
        return False
    elif len(tag.find_all(text=False)) > 0:  # no other tags inside other than text
        return False
    return True  # if valid it reaches here


def getWFSlot(productUrl):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    }

    driver = webdriver.Chrome(executable_path=pr_settings.chrome_webdriver_executable_path)
    driver.get(productUrl)
    html = driver.page_source
    soup = bs4.BeautifulSoup(html, features="html.parser")
    time.sleep(60)
    has_open_slots = False
    heart_beat = HeartBeat(600)
    while not has_open_slots:
        heart_beat.check()
        driver.refresh()
        logging.info("refreshed")
        html = driver.page_source
        # saveToFile(pr_settings.html_file_temp_folder,
        #            html)
        soup = bs4.BeautifulSoup(html, features="html.parser")
        has_open_slots = check_slots_algo1(soup)
        if has_open_slots:
            time.sleep(1400)
        else :
            time.sleep(3)
        #
        # try:
        #     open_slots = soup.find('div', class_='orderSlotExists');
        #     if open_slots is not None and open_slots.text() != "false":
        #         no_open_slots = False
        #         alert()
        #     else:
        #         logging.info('Ah! No open slots yet.')
        # except AttributeError as e:
        #     traceback.print_exc(file=sys.stdout)


def main():
    getWFSlot('https://www.amazon.com/gp/buy/shipoptionselect/handlers/display.html?hasWorkingJavascript=1')


if __name__ == '__main__':
    main()
