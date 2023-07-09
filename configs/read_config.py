import pandas as pd
import json
import os

def read_config():

    global shipping_xlsx, update_plan_col_df, pf_col_df, booking_default_df, invoice_default_df\
        , LSP_Shipping_DB, LSP_Shipping_DB_conn_str

    #   Read JSON configs file
    json_file_fullpath = os.path.join("./configs","config.json")
    with open(json_file_fullpath, "r") as f:
        config = json.load(f)

    ## Call configs and excel's sheets detail & Excel's file directory
    shipping_xlsx = config['shipping_xlsx_cf']

    # Dataframe of paring between original column in Excel and column name in sql database
    update_plan_col_df = pd.DataFrame(config['shipping_xlsx_Column']['update_plan_col_df'])
    pf_col_df = pd.DataFrame(config['shipping_xlsx_Column']['pf_col_df'])

    # Dataframe paring default value of each filed for customer
    booking_default_df = pd.DataFrame(config['shipping_xlsx_MarsDefault']['mars_booking_default_df'])
    invoice_default_df = pd.DataFrame(config['shipping_xlsx_MarsDefault']['mars_invoice_default_df'])

    ## Call configs of a SQL database
    LSP_Shipping_DB = config['LSP_Shipping_SqlDb']
    LSP_Shipping_DB_conn_str = '{}://{}:{}@{}/{}?driver={}'.format(LSP_Shipping_DB['dialect']
                                                                   , LSP_Shipping_DB['sql_username']
                                                                   , LSP_Shipping_DB['sql_password']
                                                                   , LSP_Shipping_DB['sql_host']
                                                                   , LSP_Shipping_DB['sql_database_name']
                                                                   , LSP_Shipping_DB['sql_driver'])


__all__ = ['read_config']
