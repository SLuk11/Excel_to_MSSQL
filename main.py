import time
import controllers
import logger as log
from configs import read_config as config

if __name__ == '__main__':
    ## performance counter timing parts
    tic = time.perf_counter()

    # read configs
    config.read_config()

    log.logs_dir_check(config.shipping_xlsx['log_dir'])
    log.write_log('customer_receive_process: process start')

    ## directory part

    # Directory checking
    controllers.dir_check(config.shipping_xlsx['rcv_dir'])

    # list of Excel file that have every sheet in contained_sheets list
    xlsx_list = controllers.dir_list(config.shipping_xlsx['data_dir'], config.shipping_xlsx['rcv_json_dir'])

    # Execute file when has Excel files
    if len(xlsx_list) > 0:

        # Read sheet name from configs
        sheets = config.shipping_xlsx['sheet_detail'].items()

        ## read part: turn excel table to dataframe forment
        # loop to read Excel file in xlsx_list one by one
        for excel_file in xlsx_list:

            # Create batch running number per workbook
            batch_id = controllers.create_batch_id()

            process_status = []
            # loop to read and convert each sheet (in contained_sheets list) for each Excel file
            for sheet in sheets:
                sheet_status = []
                result = False

                ## Read excel to DataFrame
                df = controllers.df_read(config.shipping_xlsx['source_dir'], excel_file
                                         , sheet[1]['sheet_name']
                                         , sheet[1]['first_col_name'])

                # Check df count or length > 0
                if len(df) > 0:
                    ## Clening data in data frame before convert to JSON format
                    df_clean = controllers.df_clean(df, sheet[1]['sheet_name'])

                    ## Execute to SQL database
                    if len(df_clean) > 0:
                        result = controllers.write2sql(config.LSP_Shipping_DB_conn_str, sheet[1]['to_table']
                                                       , df_clean, eval('config.{}'.format(sheet[1]['mapping_cols'])),
                                                       batch_id
                                                       , eval('config.{}'.format(sheet[1]['default_value'])))
                        # if complete write to SQL process
                        if result:
                            sheet_status = [sheet[1]['sheet_name'], result, ""]
                        # if NOT complete write to SQL process
                        else:
                            err_msg = 'Fail to write Excel table to SQL DB'
                            sheet_status = [sheet[1]['sheet_name'], result, err_msg]

                    else:
                        # collect error status
                        err_msg = 'Fail to converting Excel table'
                        sheet_status = [sheet[1]['sheet_name'], result, err_msg]

                else:
                    # collect error status
                    err_msg = 'Fail to reading Excel table'
                    sheet_status = [sheet[1]['sheet_name'], result, err_msg]

                # Flaf execute sheet status
                process_status.append(sheet_status)

            # Validate sheets status
            if len(process_status) > 0:
                # Get list of each sheet's status
                status = [status[1] for status in process_status]

                # if one of reading sheets was fail
                if False in status:
                    # Get error message
                    err_sheet = process_status[status.index(False)][0]
                    err_msg = process_status[status.index(False)][2]

                    # Collect fail batch transaction
                    controllers.write2batch_table(config.LSP_Shipping_DB_conn_str, batch_id, excel_file
                                                  , 0, err_msg='Sheet {} {}'.format(err_sheet, err_msg))

                    # Delete all inserted row that contain batch_id which in fail process
                    controllers.del_sql_row_bybatch(config.LSP_Shipping_DB_conn_str
                                                    , config.LSP_Shipping_DB['sql_table_list'], batch_id)

                    # move Excel file to fail folder after process do not success
                    controllers.move_file(excel_file, config.shipping_xlsx['source_dir']
                                          , config.shipping_xlsx['fail_dir'])

                # if complete process every sheets
                else:
                    # Collect success batch transaction
                    controllers.write2batch_table(config.LSP_Shipping_DB_conn_str, batch_id, excel_file, 1)

                    # Move Excel file to success folder after process success
                    controllers.move_file(excel_file, config.shipping_xlsx['source_dir']
                                          , config.shipping_xlsx['success_dir'])
    # Do not have any xlsx file in source directory
    else:
        log.write_log('{} there have no .xlsx files in folder'.format(config.shipping_xlsx['source_dir']))

    ## performance counter timing parts
    toc = time.perf_counter()
    log.write_log(f'customer_receive_process: process end in {toc - tic:0.4f} seconds')
