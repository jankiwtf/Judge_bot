import logging
import url_library
import time
from selenium import webdriver

import pathlib
from pathlib import Path


# Search link in DB
def where_url_save(url):
    indx_slash = url.find('/', 8)
    short_link = url[:indx_slash]
    if short_link in url_library.blue_site:
        return 'blue_site'
    elif short_link in url_library.brown_site:
        return 'brown_site'
    else:
        return 'С этим адресом я еще не умею работать. \nОбратись к администратору'


def data_parser(url):
    logging.info("Parsing started")

    # Run in server
    # chrome_options = Options()
    # chrome_options.add_argument('--headless')
    # chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--disable-dev-shm-usage')

    # Connect to WebDriver
    dir_path = pathlib.Path.cwd()
    path = Path(dir_path, 'venv/lib/python3.9/site-packages/selenium/webdriver/chrome/chromedriver')

    driver = webdriver.Chrome(executable_path=path)  # Run in local
    # driver = webdriver.Chrome(executable_path=path, chrome_options=chrome_options) # Run in server
    driver.get(url)

    # Waiting for page downloading
    driver.implicitly_wait(20)

    party_list = []
    info_list = []

    # Search in blue_site
    if where_url_save(url) == 'blue_site':

        # Find party
        driver.find_element_by_xpath('//*[@id="tabs"]/li[3]/span').click()  # Click button
        search_party = driver.find_elements_by_class_name('tab-content')
        for row in search_party:
            if row.text != '':
                party_list.append(row.text)

        # Find info
        driver.find_element_by_xpath('//*[@id="tabs"]/li[2]/span').click()
        search_info = driver.find_elements_by_class_name('tab-content')
        for row in search_info:
            if row.text != '':
                info_list.append(row.text)

    # Search in brown_site
    elif where_url_save(url) == 'brown_site':

        # Find party
        driver.find_element_by_xpath('//*[@id="tab3"]').click()
        party_list.append(driver.find_element_by_id('cont3').text)

        # Find info
        driver.find_element_by_xpath('//*[@id="tab2"]').click()
        info_list.append(driver.find_element_by_id("cont2").text)

    # print(info_list[0])
    bio = party_list[0].split(sep='\n')
    info = info_list[0].split(sep='\n')

    responce = [bio, info]
    driver.close()
    time.sleep(1)
    driver.quit()
    logging.info("Parsing completed!")
    return responce
