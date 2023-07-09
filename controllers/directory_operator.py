import os
import json
import shutil
import logger as log


def move_file(file_name, source_dir, destination_dir):
    try:
        # Create file origin path and destination path
        origin = '{}/{}'.format(source_dir, file_name)
        target = '{}/{}'.format(destination_dir, file_name)

        # Move file
        shutil.move(origin, target)

        log.write_log('Move file {} to {} Done'.format(file_name, destination_dir))
    except Exception as e:
        log.write_log('Move file {} to {}: ERROR {}'.format(file_name, destination_dir, e.args[0]))


def dir_check(receive_dir):
    try:
        # Check if receive_dir folder exist or not, if not create a new one
        if not os.path.exists(receive_dir):
            os.mkdir(receive_dir)
            os.mkdir('{}/success'.format(receive_dir))
            os.mkdir('{}/fail'.format(receive_dir))
            os.mkdir('{}/json'.format(receive_dir))

        return True

    except Exception as e:
        log.write_log('Directory_check: {}'.format(e.args[0]))
        # If there is NO .pdf file return empty list
        return False



## explor directory function: find .xlsx file and filter only file that contain required sheets
def dir_list(data_dir, rcv_json_dir):
    try:
        # list all json file in directory
        files = os.listdir(data_dir)

        # loop to filter only 'xlsx' prefix file
        json_list = []
        for file in files:
            # filter only .xlsx file
            if str(file.lower()).startswith('xlsx'):
                json_list.append(file)

        xlsx_list = []
        # loop thur each 'xlsx' json file
        for file_name in json_list:

            # read json file
            json_file_fullpath = os.path.join(data_dir, file_name)
            with open(json_file_fullpath, "r") as f:
                obj = json.load(f)

                # loop each pdf file detail that contain in json object
                for xlsx_detail in obj:
                    # collect data from pdf detail data as list
                    xlsx_list.append(xlsx_detail['FileName'])

            # move json file after retrieve data
            move_file(file_name, data_dir, rcv_json_dir)

        log.write_log('Listing_file_process: Done')

        # Response result
        return xlsx_list

    except Exception as e:
        log.write_log('Listing_file_process: {}'.format(e.args[0]))
        return []