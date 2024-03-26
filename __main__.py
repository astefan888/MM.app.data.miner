import code
import pandas as pd
import os


def check_for_products():
    products = code.filename_search('product_names.csv')
    if products:
        return products
    else:
        raise FileNotFoundError('product_names.csv not found')


def no_existing_links_file(product_list):
    code.compile_links(product_list)


def existing_links_file(product_list, existing_links):
    remaining_lnks = code.product_list_link_compare(product_list,
                                                    existing_links)
    code.compile_links(remaining_lnks, existing_links)


def give_links(product_list):
    lnks_fp = code.filename_search('products_and_links.csv')
    if lnks_fp:
        existing_links_file(product_list, pd.read_csv(lnks_fp))
    else:
        no_existing_links_file(product_list)
    lnks_fp = code.filename_search('products_and_links.csv')
    if lnks_fp:
        return pd.read_csv(lnks_fp)
    else:
        raise FileNotFoundError('links file not found even after compalatuion')


def existing_data_folder(existing_links, data_folder_path):

    lnks = code.remove_processed_links(existing_links, data_folder_path)
    code.extract_all_links(lnks, data_folder_path)


def no_data_folder(existing_links, data_folder_path):

    os.makedirs(data_folder_path)
    code.extract_all_links(existing_links, data_folder_path)


def __run__():

    product_list = pd.read_csv(check_for_products())

    lnks = code.select_valid_links(give_links(product_list)) # valid links only

    data_folder = 'product data'
    if os.path.isdir(data_folder):
        existing_data_folder(lnks, data_folder)
    else:
        no_data_folder(lnks, data_folder)
    print('done')


if __name__ == '__main__':
    __run__()