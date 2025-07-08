from enum import Enum

import pandas as pd

import utils

ORDER_SIZE_PERCENT = float(10)
MIN_SECONDS_BETWEEN_TRADE = 12 * 3600  # 12 hours


class PositionState(Enum):
    """ 0: flat, 1: long, -1 short
    """
    FLAT = 0
    LONG = 1
    SHORT = -1


class MarketCondition(Enum):
    """ 0: ranging, 1: bull, -1 bear
    """
    RANGING = 0
    TRENDING_UP = 1
    TRENDING_DOWN = -1


class TradingState:
    def __init__(self):
        super().__init__()

        self.position_state = PositionState.FLAT
        self.entry_price = float('NaN')
        self.position_size = float(0)
        self.target1 = float('NaN')
        self.target2 = float('NaN')
        self.stop_loss = float('NaN')
        self.target1_reached = False
        self.balance = float(0.0)
        self.unreliable_balance = float(0.0)

        #########
        self.df_trades = pd.DataFrame([])

    def get_available_balance(self):
        return self.unreliable_balance - self.position_size


def open_long(df, index, row, state):
    order_size = get_order_size(state)
    state.position_state = PositionState.LONG
    state.entry_price = row['close']
    state.position_size = order_size
    new_trade = {'time': row['time'], 'action': 'long', 'price': row['close'], 'entry_price': state.entry_price, 'position_size': state.position_size, 'target1': state.target1, 'target2': state.target2, 'stop_loss': state.stop_loss}
    state.df_trades = pd.concat([state.df_trades, pd.DataFrame([new_trade])], ignore_index=True)


def open_short(df, index, row, state):
    order_size = get_order_size(state)
    state.position_state = PositionState.SHORT
    state.entry_price = row['close']
    state.position_size = order_size
    new_trade = {'time': row['time'], 'action': 'short', 'price': row['close'], 'entry_price': state.entry_price, 'position_size': state.position_size, 'target1': state.target1, 'target2': state.target2, 'stop_loss': state.stop_loss}
    state.df_trades = pd.concat([state.df_trades, pd.DataFrame([new_trade])], ignore_index=True)


def add_to_long(df, index, row, state):
    order_size = get_order_size(state)
    state.entry_price = utils.get_entry_price_adding_to_position(state.position_size, state.entry_price, order_size, row['close'])
    state.position_size += order_size
    new_trade = {'time': row['time'], 'action': 'add_to_long', 'price': row['close'], 'entry_price': state.entry_price, 'position_size': state.position_size}
    state.df_trades = pd.concat([state.df_trades, pd.DataFrame([new_trade])], ignore_index=True)


def add_to_short(df, index, row, state):
    order_size = get_order_size(state)
    state.entry_price = utils.get_entry_price_adding_to_position(state.position_size, state.entry_price, order_size, row['close'])
    state.position_size += order_size
    new_trade = {'time': row['time'], 'action': 'add_to_short', 'price': row['close'], 'entry_price': state.entry_price, 'position_size': state.position_size}
    state.df_trades = pd.concat([state.df_trades, pd.DataFrame([new_trade])], ignore_index=True)


def close_position(df, index, row, state):
    islong = state.position_state == PositionState.LONG
    pnl_percentage = utils.get_pnl_percent(state.entry_price, row['close'], islong)

    pnl = pnl_percentage*state.position_size/100
    if not pd.isna(pnl):
        state.balance += pnl

    if state.balance < 0:
        raise Exception("Liquidated, balance is negative!")

    #######
    state.position_state = PositionState.FLAT
    state.entry_price = float('NaN')
    state.target1 = float('NaN')
    state.target2 = float('NaN')
    state.stop_loss = float('NaN')
    state.target1_reached = False
    state.position_size = float(0)
    new_trade = {'time': row['time'], 'action': 'close', 'price': row['close'], 'entry_price': state.entry_price, 'position_size': state.position_size}
    state.df_trades = pd.concat([state.df_trades, pd.DataFrame([new_trade])], ignore_index=True)


def get_order_size(state):
    order_size = state.get_available_balance() * ORDER_SIZE_PERCENT / 100
    return order_size


def partial_close_position(df, index, row, state):
    # # if position size is too small, just close it
    # order_size = state.get_available_balance() * ORDER_SIZE_PERCENT / 100
    # if state.position_size <= order_size:
    #     close_position(df, index, row, state)
    #     return

    ##########################################
    # close 50% of position_size
    islong = state.position_state == PositionState.LONG
    pnl_percentage = utils.get_pnl_percent(state.entry_price, row['close'], islong)

    pnl = (pnl_percentage*state.position_size/100)/2
    if not pd.isna(pnl):
        state.balance += pnl

    if state.balance < 0:
        raise Exception("Liquidated, balance is negative!")

    #######
    state.position_size /= 2
    new_trade = {'time': row['time'], 'action': 'partial_close', 'price': row['close'], 'entry_price': state.entry_price, 'position_size': state.position_size}
    state.df_trades = pd.concat([state.df_trades, pd.DataFrame([new_trade])], ignore_index=True)


def plot_long_short_close(df_trades, fplt, ax):
    if df_trades.shape[0] > 0:
        df_trades = df_trades.astype({'time': 'datetime64[ms]', 'action': object, 'price': float})
        df_trades['time'] = df_trades['time'].dt.tz_localize(None)
        df_long = df_trades[df_trades['action'] == 'long']
        df_short = df_trades[df_trades['action'] == 'short']
        df_close = df_trades[df_trades['action'] == 'close']
        df_partial_close = df_trades[df_trades['action'] == 'partial_close']
        df_add_to_long = df_trades[df_trades['action'] == 'add_to_long']
        df_add_to_short = df_trades[df_trades['action'] == 'add_to_short']

        df_long.reset_index(drop=True, inplace=True)
        df_short.reset_index(drop=True, inplace=True)
        df_close.reset_index(drop=True, inplace=True)
        df_partial_close.reset_index(drop=True, inplace=True)
        df_add_to_long.reset_index(drop=True, inplace=True)
        df_add_to_short.reset_index(drop=True, inplace=True)

        if df_long.shape[0] > 0:
            fplt.plot(df_long['time'], df_long['price'], ax=ax, color='#4a5', width=3, style='^', legend='long')
        if df_short.shape[0] > 0:
            fplt.plot(df_short['time'], df_short['price'], ax=ax, color='#b94a3e', width=3, style='v', legend='short')
        if df_close.shape[0] > 0:
            fplt.plot(df_close['time'], df_close['price'], ax=ax, color='#269898', width=3, style='o', legend='close')
        if df_partial_close.shape[0] > 0:
            fplt.plot(df_partial_close['time'], df_partial_close['price'], ax=ax, color='#269898', width=1.5, style='o', legend='df_partial_close')
        if df_add_to_long.shape[0] > 0:
            fplt.plot(df_add_to_long['time'], df_add_to_long['price'], ax=ax, color='#4a5', width=1.5, style='^', legend='add_to_long')
        if df_add_to_short.shape[0] > 0:
            fplt.plot(df_add_to_short['time'], df_add_to_short['price'], ax=ax, color='#b94a3e', width=1.5, style='v', legend='add_to_short')