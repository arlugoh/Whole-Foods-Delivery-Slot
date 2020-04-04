import bs4

from selenium import webdriver

import sys
import time
import os
import traceback
import logging
import pr_settings

logging.basicConfig(format='%(asctime)s %(levelname)s : %(message)s', level=logging.INFO)


def getWFSlot(productUrl):
   headers = {
       'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
   }

   driver = webdriver.Chrome(executable_path=pr_settings.chrome_webdriver_executable_path)
   driver.get(productUrl)           
   html = driver.page_source
   soup = bs4.BeautifulSoup(html, features="html.parser")
   time.sleep(60)
   no_open_slots = True
   heart_beat_freq_in_secs = 600
   starting=time.time()
   while no_open_slots:
      elapsed = time.time()-starting
      logging.debug('elapsed sec : ' + str(elapsed))
      if elapsed > 600:
        os.system('say "Program still alive"')
        starting=time.time()
      
      driver.refresh()
      logging.info("refreshed")
      html = driver.page_source
      soup = bs4.BeautifulSoup(html, features="html.parser")
      time.sleep(2)

      try:
         open_slots = soup.find('div', class_ ='orderSlotExists');
         
         if open_slots != None and open_slots.text() != "false":
            logging.info('SLOTS OPEN!')
            os.system('say "Slots for delivery opened!"')
            no_open_slots = False
            time.sleep(1400)
         else :
            logging.info('Ah! No open slots yet.')
      except AttributeError as e:
         traceback.print_exc(file=sys.stdout)

getWFSlot('https://www.amazon.com/gp/buy/shipoptionselect/handlers/display.html?hasWorkingJavascript=1')


