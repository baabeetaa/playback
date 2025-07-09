import finplot as fplt

class PlayBackState:
    def __init__(self):
        self.index = 0  # current index


class AVWAP:
    def __init__(self, anchor_datetime=None):
        self.anchor_datetime = anchor_datetime
        self.df_anchored = None
        self.plot_avwap = None

    def calculate(self, df):
        # Filter data from the anchor point
        self.df_anchored = df[df.time >= self.anchor_datetime].copy()
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

    def plot(self, ax):
        if self.plot_avwap is not None:
            ax.removeItem(self.plot_avwap)
        self.plot_avwap = fplt.plot(self.df_anchored['time'], self.df_anchored['avwap'], ax=ax, color='#0000ff', width=1)