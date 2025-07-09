from datetime import datetime


class PlayBackState:
    def __init__(self):
        self.index = 0  # current index


class AVWAP:
    def __init__(self, anchor_datetime=None, df=None):
        self.anchor_datetime = anchor_datetime
        self.df = df
        self.df_anchored = None

    def calculate(self):
        # Filter data from the anchor point
        self.df_anchored = self.df[self.df.time >= self.anchor_datetime].copy()
        self.df_anchored = self.df_anchored.astype({'time': 'datetime64[ms]'})
        self.df_anchored['time'] = self.df_anchored['time'].dt.tz_localize(None)

        # Calculate price * volume
        self.df_anchored['price_volume'] = self.df_anchored['close'] * self.df_anchored['volume']

        # Calculate cumulative sums
        self.df_anchored['cumulative_price_volume'] = self.df_anchored['price_volume'].cumsum()
        self.df_anchored['cumulative_volume'] = self.df_anchored['volume'].cumsum()

        # Calculate AVWAP
        self.df_anchored['avwap'] = self.df_anchored['cumulative_price_volume'] / self.df_anchored['cumulative_volume']

        # need this for fplt.plot to work
        self.df_anchored.reset_index(drop=True, inplace=True)