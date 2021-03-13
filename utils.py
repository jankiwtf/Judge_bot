import logging
import url_library
import time
from selenium import webdriver


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
    logging.info("Browser in run!")

    # подключение браузера и прописывание адреса к драйверу
    driver = webdriver.Chrome('/Users/janki/Desktop/Python/judge_bot/venv/lib/python3.9/site-packages/selenium/'
                              'webdriver/chrome/chromedriver')
    driver.get(url)

    # ждем пока загрузится страница
    driver.implicitly_wait(15)

    bio_list = []
    info_list = []

    # Search in blue_site
    if where_url_save(url) == 'blue_site':

        # Find players data
        driver.find_element_by_xpath('//*[@id="tabs"]/li[3]/span').click()  # Click button
        search_bio = driver.find_elements_by_class_name('tab-content')
        for row in search_bio:
            if row.text != '':
                bio_list.append(row.text)

        # Find main data
        driver.find_element_by_xpath('//*[@id="tabs"]/li[2]/span').click()
        search_info = driver.find_elements_by_class_name('tab-content')
        for row in search_info:
            if row.text != '':
                info_list.append(row.text)

    # Search in brown_site
    elif where_url_save(url) == 'brown_site':

        # Find players data
        driver.find_element_by_xpath('//*[@id="tab3"]').click()
        bio_list.append(driver.find_element_by_id('cont3').text)

        # Find main data
        driver.find_element_by_xpath('//*[@id="tab2"]').click()
        info_list.append(driver.find_element_by_id('cont2').text)

    bio = bio_list[0].split(sep='\n')
    info = info_list[0].split(sep='\n')
    responce = [bio, info]

    driver.close()
    time.sleep(1)
    driver.quit()
    logging.info("Browser closed!")
    return responce
