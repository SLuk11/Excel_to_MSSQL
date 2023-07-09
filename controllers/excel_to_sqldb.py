import pandas as pd
import numpy as np
import sqlalchemy
import uuid
import fnmatch2
import logger as log


## read function: read excel data then convert to dataframe
def df_read(source_dir, excel_name, sheet, first_col_name):
    try:
        colhead_row_id = 0
        path = "{}/{}".format(source_dir, excel_name)

        # read Excel file
        df = pd.read_excel(path, sheet_name=sheet)

        # check first row contain table or not, by checking first column's name
        if df.columns[0] != first_col_name:
            for row in range(0, len(df)):
                colhead_row_id = row
                if df.iloc[row][0] == first_col_name:
                    break

            # turn row value (match first column name) to be table header
            df.columns = df.iloc[colhead_row_id]

            # skip rows before table header
            df = df.iloc[colhead_row_id + 1:]

        log.write_log('{}_sheet_{} Reading process: Done'.format(excel_name, sheet))

        # Response result
        return df
    except Exception as e:
        log.write_log('{}_sheet_{} Reading process: {}'.format(excel_name, sheet, e.args[0]))
        return []


## cleaning function: prepare data before convert to JSON format
def df_clean(df, sheet_name):
    try:
        ## check table header have duplicate name or not
        cols = pd.Series(df.columns)
        for dup in cols[cols.duplicated()].unique():
            # if duplicate name occur, change name by add number
            cols[cols[cols == dup].index.values.tolist()] = [dup + '.' + str(i) if i != 0
                                                             else dup for i in range(sum(cols == dup))]
        # rename table columns with the cols list.
        df.columns = cols
        ## cleaning blank data
        df = df[df[df.columns[0]].notna()]
        # Convert all values to strings
        df_str = df.applymap(str)
        # Clean dataframe
        df_str.replace('0', np.nan, inplace=True)
        df_str.replace(' ', np.nan, inplace=True)
        df_str.replace('nan', np.nan, inplace=True)
        # Reset row index
        df_clean = df_str.reset_index(drop=True)
        ## special case: edit condition for each sheet
        match sheet_name:
            case 'Update Plan':
                pf_index = df_clean.columns.get_loc('Prof. Inv ')
                df_clean = df_clean[df_clean[df_clean.columns[pf_index]].notna()]
                df_clean['SI Cutt Off DateTime'] = pd.to_datetime(
                    df_clean['SI Cutt Off Date'].astype(str) + ' ' + df_clean['SI Cutt Off Time'].astype(str))
            case 'PF':
                cols_pf = pd.Series(df_clean.columns)
                for i, col in enumerate(cols_pf):
                    if fnmatch2.fnmatch2(col, '*Item'):
                        cols_pf[i] = 'Item'
                    elif fnmatch2.fnmatch2(col, '*Net value'):
                        cols_pf[i] = 'Net value'
                    elif fnmatch2.fnmatch2(col, '*Cost'):
                        cols_pf[i] = 'Cost'
                    elif fnmatch2.fnmatch2(col, '*Volume'):
                        cols_pf[i] = 'Volume'
                    elif fnmatch2.fnmatch2(col, '*Net weight'):
                        cols_pf[i] = 'Net weight'
                    elif fnmatch2.fnmatch2(col, '*Gross value'):
                        cols_pf[i] = 'Gross value'
                df_clean.columns = cols_pf
                pf_index = df_clean.columns.get_loc('Bill.Doc.')
                df_clean = df_clean[df_clean[df_clean.columns[pf_index]].notna()]
                df_clean['Sales Doc.'] = (df_clean['Sales Doc.'].astype(float)).apply(np.int64)
                df_clean['Bill.Doc.'] = (df_clean['Bill.Doc.'].astype(float)).apply(np.int64)
                df_clean['Item'] = (df_clean['Item'].astype(float)).apply(np.int64)
                df_clean['Billed Quantity'] = (df_clean['Billed Quantity'].astype(float)).apply(np.int64)
                df_clean['Material'] = (df_clean['Material'].astype(float)).apply(np.int64)
                df_clean['Ref. Doc.'] = (df_clean['Ref. Doc.'].astype(float)).apply(np.int64)
                df_clean['Di'] = (df_clean['Di'].astype(float)).apply(np.int64)
                df_clean['Required quantity'] = (df_clean['Required quantity'].astype(float)).apply(np.int64)
                df_clean['Denominator'] = (df_clean['Denominator'].astype(float)).apply(np.int64)
                df_clean['Pricing Dt'] = pd.to_datetime(df_clean['Pricing Dt'], dayfirst=True).astype(str)
                df_clean['Created On'] = pd.to_datetime(df_clean['Created On'], dayfirst=True).astype(str)

        log.write_log('sheet_{} Cleaning process: Done'.format(sheet_name))

        # Response result
        return df_clean

    except Exception as e:
        log.write_log('sheet_{} Cleaning process: {}'.format(sheet_name, e.args[0]))
        return []


def create_batch_id():
    return uuid.uuid4()


def write2batch_table(conn_str, batch_id, excel_file, complete_status, err_msg = ""):
    # collect batch transaction
    try:
        if complete_status == 1:
            batch_col = {'message_type': 'receive', 'batch_no': [batch_id], 'excel_file': [excel_file]
                , 'is_complete': 1}
        else:
            batch_col = {'message_type': 'receive', 'batch_no': [batch_id], 'excel_file': [excel_file]
                , 'is_complete': 0, 'remark': "{}".format(err_msg)}
        batch_df = pd.DataFrame(batch_col)
        engine = sqlalchemy.create_engine(conn_str)
        batch_df.to_sql('rcv_customer_batch', engine, if_exists='append', index=False)

        return True

    except Exception as e:
        log.write_log('Write to batch table {}'.format(e.args[0]))

        return False


def write2sql(connection_string, table_name, df, col_df, batch_id, mars_default_value_df):
    try:
        # Filter only target column
        df_filter = df[col_df['origin_col_name'].values.tolist()]
        # Rename column to match SQL table
        df_filter.columns = col_df['sql_col_name'].values.tolist()
        # add batch_no column to data frame
        df_filter['batch_no'] = batch_id
        # add default_value column to dataframe
        for index in range(0, len(mars_default_value_df)):
            df_filter[mars_default_value_df['sql_col_name'][index]] = mars_default_value_df['default_value'][index]

        # Create the SQLAlchemy engine
        engine = sqlalchemy.create_engine(connection_string)
        # Write DataFrame to the SQL Server database
        df_filter.to_sql(table_name, engine, if_exists='append', index=False)
        # Dispose of the engine
        engine.dispose()
        log.write_log('SQL_{}_table Insert to SQL process: Done'.format(table_name))

        return True

    except Exception as e:
        log.write_log('SQL_{}_table Insert to SQL process: {}'.format(table_name, e.args[0]))
        return False


## Delete all inserted row in tabl_list that contain specific batch_id value
def del_sql_row_bybatch(connection_string, table_list, batch_id):
    try:
        engine = sqlalchemy.create_engine(connection_string)
        connection = engine.connect()
        for table in table_list:
            # create mask as metadata of each table
            mask = sqlalchemy.Table(table, sqlalchemy.MetaData(), autoload_with=engine)
            # create statement to delete row of each table depend on bach_id value
            stmt = mask.delete().where(
                mask.c.batch_no == '{}'.format(batch_id))
            connection.execute(stmt)
            connection.commit()

        log.write_log('Batch_no_{} Delete row process: Done'.format(batch_id))
    except Exception as e:
        log.write_log('Batch_no_{} Delete row process: {}'.format(batch_id, e.args[0]))
