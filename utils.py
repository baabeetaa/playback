import math
import datetime
import pandas as pd

str_datetime_format = '%Y-%m-%dT%H:%M:%S'  # '%Y-%m-%dT%H:%M:%S.%fZ'


def datetime_to_str(dt, s_format=str_datetime_format):
    return dt.strftime(s_format)


def str_to_datetime(s, s_format=str_datetime_format):
    return datetime.datetime.strptime(s, s_format).replace(tzinfo=datetime.timezone.utc)


def get_entry_price_adding_to_position(current_position_size, current_price, added_position_size, added_price):
    return (current_position_size*current_price + added_position_size*added_price)/(current_position_size + added_position_size)


def get_pnl_percent(entry_price, price, is_long=True):
    """
    eg.,
    entry_price | price  | long  | short
    ------------+--------+-------+------
    100         | 120    |  20%  | -20%
    100         | 80     | -20%  |  20%

    :param entry_price:
    :param price:
    :param is_long:
    :return:
    """
    pnl_percentage = float(0.0)  # profit and loss

    if is_long:
        pnl_percentage = (price-entry_price)/entry_price
    else:
        pnl_percentage = (entry_price-price)/entry_price

    return float(100)*pnl_percentage


def timeframe_text_to_seconds(s):
    if s == 'm1':
        return 60
    elif s == 'm5':
        return 300
    elif s == 'm15':
        return 900
    elif s == 'm30':
        return 1800
    elif s == 'h1':
        return 3600
    elif s == 'h2':
        return 7200
    elif s == 'h4':
        return 14400
    elif s == 'd1':
        return 86400
    else:
        raise ValueError('Invalid value!')


def timeframe_seconds_to_text(s):
    if s == 60:
        return 'm1'
    elif s == 300:
        return 'm5'
    elif s == 900:
        return 'm15'
    elif s == 1800:
        return 'm30'
    elif s == 3600:
        return 'h1'
    elif s == 7200:
        return 'h2'
    elif s == 14400:
        return 'h4'
    elif s == 86400:
        return 'd1'
    else:
        raise ValueError('Invalid value!')


def load_data(filenames):
    df = None
    for csv_file in filenames:
        df_tmp = pd.read_csv(csv_file, index_col=None)  # load data
        if df is None:
            df = df_tmp
        else:
            df = pd.concat([df, df_tmp], ignore_index=True)
    return df