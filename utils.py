import logging
import url_library
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import pathlib
from pathlib import Path


def data_parser(url):
    global party, party_info
    logging.info("Parsing started")

    # Run in server
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # Connect to WebDriver
    dir_path = pathlib.Path.cwd()
    path = Path(dir_path, 'venv/lib/python3.9/site-packages/selenium/webdriver/chrome/chromedriver')
    # driver = webdriver.Chrome(executable_path=path)  # Run in local

    # path = Path('/usr/bin/chromedriver')
    driver = webdriver.Chrome(executable_path=path, chrome_options=chrome_options)  # Run in server
    driver.get(url)

    # Waiting for page downloading
    driver.implicitly_wait(20)

    party_list = []
    info_list = []
    site_kind = url_library.where_url_save(url)
    # Search in blue_site
    if site_kind == 'blue_site' or site_kind == 'blue_site_v2':
        # Find party
        driver.find_element_by_xpath('//*[@id="tabs"]/li[3]/span').click()  # Click button
        search_party = driver.find_elements_by_class_name('tab-content')
        bio = str()
        for row in search_party:
            if row.text != '':
                bio = row.text.split(sep='\n')

        # Find info
        driver.find_element_by_xpath('//*[@id="tabs"]/li[2]/span').click()
        search_info = driver.find_elements_by_class_name('tab-content')
        info = str()
        for row in search_info:
            if row.text != '':
                info = row.text.split(sep='\n')

        if site_kind == 'blue_site':
            party = f'Стороны: {bio[2][45:]}'
        else:
            party = f'Стороны: {bio[-2]}, {bio[-1]}'
        party_info = f'- {info[-2]}\n- {info[-1]}'

    # Search in brown_site
    elif site_kind == 'brown_site':
        # Find party
        driver.find_element_by_xpath('//*[@id="tab3"]').click()
        party_list.append(driver.find_element_by_id('cont3').text)

        # Find info
        driver.find_element_by_xpath('//*[@id="tab2"]').click()
        info_list.append(driver.find_element_by_id("cont2").text)

        bio = party_list[0].split(sep='\n')
        bio = bio[2:]
        info = info_list[0].split(sep='\n')

        party = f'Стороны: {", ".join(bio)}'
        party_info = f'- {info[-2]},\n- {info[-1]}'

    # Search in brown_site_v2
    elif site_kind == 'brown_site_v2':
        # Find party
        driver.find_element_by_xpath('//*[@id="tab4"]').click()
        party_list.append(driver.find_element_by_id('cont4').text)

        # Find info
        driver.find_element_by_xpath('//*[@id="tab2"]').click()
        info_list.append(driver.find_element_by_id("cont2").text)

        bio = party_list[0].split(sep='\n')
        bio = bio[2:]
        info = info_list[0].split(sep='\n')

        party = f'Стороны: {", ".join(bio)}'
        if len(info_list) > 2:
            party_info = f'- {info[-2]},\n- {info[-1]}'
        else:
            party_info = f'- {info[-1]}'

    # Search in brown_site_short
    # elif site_kind == 'brown_site_short':
    #     print('test1')
    #     # time.sleep(15)
    #     # print('test2')
    #     # Find party
    #     driver.find_element_by_xpath('//*[@id="cardContainer"]/div[2]/div/div/ul/li[1]').click()
    #     print('test3')
    #     party_list.append(driver.find_element_by_id('cardContainer').text)
    #     print('test4')
    #     print(party_list)
    #
    #     # Find info
    #     driver.find_element_by_xpath('//*[@id="cardContainer"]/div[2]/div/div/ul/li[2]').click()
    #     info_list.append(driver.find_element_by_id("cardContainer").text)
    #
    #     bio = party_list[0].split(sep='\n')
    #     info = info_list[0].split(sep='\n')
    #     party = f'Стороны: {bio[-2]}, {bio[-1]}'
    #     party_info = f'- {info[-2]},\n- {info[-1]}'

    elif site_kind == 'grey_site':
        # Find party and info
        search_info = driver.find_elements_by_class_name("table-row")
        for row in search_info:
            if row.text != '':
                info_list.append((row.text.replace('\n', ', ')))

        party = f'Стороны: {info_list[0]}, {info_list[1]}'
        party_info = f'- {info_list[-2]},\n- {info_list[-1]}'

    elif site_kind == 'white_site':
        # Find party
        search_party = driver.find_elements_by_class_name('detail-cart')
        bio = search_party[0].text.split(sep='\n')
        party_index = bio.index('Стороны') + 1
        party = bio[party_index] + ", " + bio[party_index + 1]

        # Find info
        search_info = driver.find_elements_by_class_name('custom_table')
        info = search_info[0].text.split(sep='\n')
        if len(info) > 4:
            party_info = f'- {", ".join(info[-6:-3])}\n' \
                         f'- {", ".join(info[-3:])}'
        else:
            party_info = f'- {", ".join(info[1:])}'

    elif site_kind == 'red_site':
        # Find party
        driver.find_element_by_xpath('//div/label[2]').click()
        search_party = driver.find_elements_by_class_name("casecard")
        for row in search_party:
            if row.text != '':
                party_list = row.text.split(sep="\n")

        # Find info
        driver.find_element_by_xpath('//div/label[5]').click()
        search_info = driver.find_elements_by_class_name("casecard")
        for row in search_info:
            if row.text != '':
                info_list = row.text.split(sep="\n")

        party = party_list[-2] + "; " + party_list[-1]
        if len(info_list) > 2:
            party_info = f'- {info_list[-2]},\n- {info_list[-1]}'
        else:
            party_info = f'- {info_list[-1]}'
    else:
        return False

    responce = [party, party_info]
    driver.close()
    time.sleep(1)
    driver.quit()
    logging.info("Parsing completed!")
    return responce
