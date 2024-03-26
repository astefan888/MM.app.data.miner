from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from subprocess import getoutput
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import os
import requests
from urllib.parse import urlparse
import pandas as pd
import shutil


def give_driver():
    options = Options()
    options.binary_location = getoutput("find /snap/firefox -name firefox").split("\n")[-1]

    driver = webdriver.Firefox(service=
            Service(executable_path = getoutput("find /snap/firefox -name geckodriver").split("\n")[-1]),
            options = options)
    
    return driver


def search(search_term):

    driver = give_driver()

    driver.get("https://eastern-star.com/")

    clickable = driver.find_element(By.NAME, "search_keyword")
    print(clickable)
    ActionChains(driver)\
            .move_to_element(clickable)\
            .pause(1)\
            .click_and_hold()\
            .pause(1)\
            .send_keys(search_term)\
            .send_keys(Keys.RETURN)\
            .perform()

    time.sleep(5)

    all_links = []
    links = driver.find_elements(By.TAG_NAME, "a")
    for link in links:
        href = link.get_attribute("href")
        if href:
            # print("Link:", href)
            all_links.append(href)

    driver.quit()

    search_res = [x for x in set(all_links) if 'display' in x]
    if search_res:
        pass
    else:
        raise KeyError(search_term, ' not found')

    if len(search_res) > 1:
        print(search_res)
        raise KeyError(search_term, ' gives multiple res, please specify')

    return search_res[0]


def compile_links(product_names, existing_links=[False]):

    products_and_links = []

    products_remaning = len(product_names)
    print('number of products to produce links for ', products_remaning)
    for pn in product_names:

        try:
            link = search(pn)
        except Exception as e:
            link = e

        products_and_links.append([pn, link])

        products_remaning -= 1
        print('number of products to produce links for ', products_remaning)

    products_and_links = pd.DataFrame(products_and_links,
                                      columns=['item', 'link'])

    if any(existing_links):
        products_and_links = pd.concat([existing_links, products_and_links],
                                       axis=0)

    products_and_links.set_index('item').to_csv('products_and_links.csv')


def product_list_link_compare(product_list, existing_links):

    links = existing_links['item']
    products = product_list['item']

    return list(set(products).difference(links))


def extract_text(loaded_driver, save_fp):

    selected_text = loaded_driver.execute_script("return document.body.innerText;")

    def limit_str(string, first_key_term, last_key_term):
        return string[string.find(first_key_term)+len(first_key_term): string.find(last_key_term)]

    txt = limit_str(selected_text, 'Other Parts', 'Chuzhou Eastern Star')

    with open(os.path.join(save_fp, 'product description.txt'), 'w') as f:
        f.write(txt)


def extract_imgs(loaded_driver, save_fp):

    images = loaded_driver.find_elements(By.TAG_NAME, "img")

    # Create a directory to store the downloaded images
    save_fp = os.path.join(save_fp, 'downloaded_images')
    os.makedirs(save_fp, exist_ok=True)

    img_blacklist = ['166795715042179300.jpg', '160818754145810500.jpg',
                     'aside_ico_email.svg']

    #Download each image
    for image in images:
        src = image.get_attribute("src")
        if src:
            img_fn = os.path.basename(urlparse(src).path)
            if img_fn in img_blacklist:
                continue
            # Parse the URL to get the filename
            filename = os.path.join(save_fp, img_fn)
            # Download the image
            response = requests.get(src)
            with open(filename, "wb") as f:
                f.write(response.content)
                # print("Downloaded:", filename)


def extract_from_link(link, save_fp):

    driver = give_driver()
    driver.get(link)

    extract_text(driver, save_fp)
    extract_imgs(driver, save_fp)

    driver.quit()


def extract_all_links(existing_links, data_folder):

    links = {product_name_to_folder_name(k, to_folder=True):
             v for k, v in zip(existing_links['item'],
             existing_links['link'])}
    total_left = len(links)
    print('total number of products left to extract ', total_left)
    for item_name, lnk in links.items():

        print(item_name)
        loop_folder = os.path.join(data_folder, item_name)
        os.makedirs(loop_folder, exist_ok=True)

        extract_from_link(lnk, loop_folder)

        total_left -= 1
        print('total number of products left to extract ', total_left)


def select_valid_links(existing_links):

    def validity_condition(link):
        return 'eastern-star.com' in link

    return existing_links[list(map(validity_condition, existing_links['link']))]


def product_name_to_folder_name(name, to_folder):
    if to_folder:
        return name.replace('/', '_')
    else:
        return name.replace('_', '/')


def remove_processed_links(existing_links, data_folder_path):

    existing_folders = [product_name_to_folder_name(x, to_folder=False)
                        for x in os.listdir(data_folder_path)
                        if os.path.isdir(os.path.join(data_folder_path, x))]

    # removal of the latest made folder, in case of process termination 
    last_made_folder = max([os.path.join(data_folder_path, x)
                            for x in os.listdir(data_folder_path)],
                            key=os.path.getmtime)
    shutil.rmtree(last_made_folder)
    last_made_folder = os.path.basename(last_made_folder)
    last_made_folder = product_name_to_folder_name(last_made_folder,
                                                   to_folder=False)

    existing_folders = list(set(existing_folders).difference([last_made_folder]))

    return existing_links.loc[~existing_links['item'].isin(existing_folders)]


def filename_search(search_filename):
    for dirpath, dirnames, filenames in os.walk(os.getcwd()):
        if search_filename in filenames:
            return os.path.join(dirpath, search_filename)
