from configs import read_config as config
from datetime import datetime
import os


def write_log(message):

    # create log file (one log per day)
    log_dir = config.shipping_xlsx['log_dir']
    today = datetime.today().strftime('%Y-%m-%d')
    file_fullname = os.path.join(log_dir, "{}_event.log".format(today))
    f = open(file_fullname, 'a')
    # log contain datetime file_name and event
    f.write("{} {}\n".format(datetime.today().strftime('%Y-%m-%d %H:%M:%S'), message))
    f.close()


def write_excel_log(excel_file, message):
    # create log file (one log per excel)
    log_dir = config.shipping_xlsx['log_dir']
    today = datetime.today().strftime('%Y-%m-%d')
    excel_name = excel_file.split(".")[0]
    file_fullname = os.path.join(log_dir, today, "{}_{}.log".format(today, excel_name))
    f = open(file_fullname, 'a')
    # log contain datetime file_name and event
    f.write("{} {}\n".format(datetime.today().strftime('%Y-%m-%d %H:%M:%S'), message))
    f.close()


def logs_dir_check(log_dir):
    # Check if log_dir folder exist or not, if not create a new one
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    today = datetime.today().strftime('%Y-%m-%d')
    if not os.path.exists(f'{log_dir}/{today}'):
        os.mkdir(f'{log_dir}/{today}')
