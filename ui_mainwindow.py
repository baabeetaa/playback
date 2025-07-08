import datetime
import random
from datetime import timedelta

import finplot as fplt
import pandas as pd
import pyqtgraph as pg
import requests
from PyQt6.QtCore import QSize, Qt, QRectF
from PyQt6.QtGui import QAction, QShortcut, QKeySequence
from PyQt6.QtWidgets import QMainWindow, QSizePolicy, QStatusBar, QMessageBox, QWidget, QLabel, QToolBar, QSplitter, \
    QVBoxLayout, QTabWidget, QPushButton

import trading
import utils
from playback import PlayBackState


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

        # variables
        self.selectedMouseTool = "Cursor"
        self.df_full = pd.DataFrame([])
        self.df = pd.DataFrame([])
        self.playback_state = PlayBackState()

        # trade_state
        self.trade_state = trading.TradingState()
        self.trade_state.balance = float(1000.0)  # set initial balance
        self.trade_state.unreliable_balance = self.trade_state.balance

        self.ref_entry_line = None

        self.total_trades_count = 0

        self.draw_rect = None

    def init_ui(self):
        self.resize(QSize(3200, 1600))
        self.setWindowTitle("PlayBack")
        self.create_menubar()
        self.create_toolbar()
        self.create_statusbar()

        fplt.FinViewBox.mouseRightDrag = self.on_chart_right_drag

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self.splitter)
        self.create_left_panels()
        self.create_charts()

        # Define the shortcut
        shortcut_play_next = QShortcut(QKeySequence("Ctrl+N"), self)
        shortcut_play_next.activated.connect(self.on_play_next)

        shortcut_open_random_file = QShortcut(QKeySequence("Ctrl+R"), self)
        shortcut_open_random_file.activated.connect(self.on_file_open_random_click)

    def create_menubar(self):
        mainmenu = self.menuBar()
        mainmenu.setVisible(True)
        mainmenu.setNativeMenuBar(False)  # Disables the global menu bar on MacOS

        ####################
        # File
        filemenu = mainmenu.addMenu('File')

        # file_open_random_action
        file_open_random_action = QAction("Open Random", self)
        filemenu.addAction(file_open_random_action)
        file_open_random_action.triggered.connect(self.on_file_open_random_click)

        filemenu.addSeparator()

        # file_close_action
        file_close_action = QAction("Close", self)
        filemenu.addAction(file_close_action)

        ####################
        # Tools
        tools_menu = mainmenu.addMenu('Tools')

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        ####################################################################################
        # drawing tools
        # Cursor
        playNext = QAction("Next", self)
        playNext.setStatusTip("Next")
        playNext.triggered.connect(self.on_play_next)
        toolbar.addAction(playNext)

    def create_statusbar(self):
        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)

        # lbl_status_bar_msg
        self.lbl_status_bar_msg = QLabel("lbl_status_bar_msg")
        self.statusBar.addPermanentWidget(self.lbl_status_bar_msg)

    def create_left_panels(self):
        # ###############################################
        # tab_trade
        layout_trade = QVBoxLayout()
        layout_trade.setSpacing(20)

        btn_market_long = QPushButton("Market Long")
        btn_market_long.setStyleSheet("background-color: green;")
        btn_market_long.clicked.connect(self.on_btn_market_long_clicked)
        layout_trade.addWidget(btn_market_long)

        btn_market_short = QPushButton("Market Short")
        btn_market_short.setStyleSheet("background-color: red;")
        btn_market_short.clicked.connect(self.on_btn_market_short_clicked)
        layout_trade.addSpacing(20)
        layout_trade.addWidget(btn_market_short)

        btn_close_trade = QPushButton("Close Trade")
        btn_close_trade.clicked.connect(self.on_btn_close_trade_clicked)
        layout_trade.addSpacing(20)
        layout_trade.addWidget(btn_close_trade)

        # account balance
        self.lbl_account_balance = QLabel("Balance: 123456")
        layout_trade.addSpacing(20)
        layout_trade.addWidget(self.lbl_account_balance)

        # lbl_trade
        self.lbl_trade = QLabel("Trade: FLAT")
        layout_trade.addSpacing(20)
        layout_trade.addWidget(self.lbl_trade)

        # lbl_entry
        self.lbl_entry = QLabel("Entry: 123456")
        layout_trade.addWidget(self.lbl_entry)

        # lbl_position_size
        self.lbl_position_size = QLabel("Size: 123456")
        layout_trade.addWidget(self.lbl_position_size)

        # lbl_pnl_unreliable
        self.lbl_pnl_unreliable = QLabel("Unreliable PnL: 123456")
        layout_trade.addWidget(self.lbl_pnl_unreliable)

        # # pnl
        # self.lbl_pnl = QLabel("PnL: 123456")
        # layout_trade.addWidget(self.lbl_pnl)

        # lbl_total_trades_count
        self.lbl_total_trades_count = QLabel("Total Trades Count: 0")
        layout_trade.addSpacing(30)
        layout_trade.addWidget(self.lbl_total_trades_count)

        layout_trade.addStretch()  # Add a stretch to push everything to the top

        tab_trade = QWidget()
        tab_trade.setLayout(layout_trade)

        # ###############################################
        # tab_widget
        tab_widget = QTabWidget()
        tab_widget.setTabPosition(QTabWidget.TabPosition.West)
        tab_widget.setDocumentMode(True)
        tab_widget.setMinimumWidth(480)
        tab_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        tab_widget.addTab(tab_trade, "Trade")

        self.splitter.addWidget(tab_widget)

    def create_charts(self):
        fplt.display_timezone = datetime.timezone.utc
        # fplt.lod_candles = 300000  # Level of Detail (LoD) to fix some candles not being displayed
        # fplt.background = '#444444'
        fplt.odd_plot_background = '#f3f6f4'

        # plot price
        """
        create 1 rows: 
            0: for candle, 
        """
        self.axs = fplt.create_plot('USDT-BTC', rows=2, init_zoom_periods=10, yscale='linear')
        self.axo = self.axs[0].overlay()
        self.splitter.addWidget(self.axs[0].vb.win)

        # set rows height
        fplt.axis_height_factor[0] = 5
        fplt.axis_height_factor[1] = 1
        # fplt.axis_height_factor[2] = 1
        # fplt.axis_height_factor[3] = 1
        # fplt.axis_height_factor[4] = 1
        # fplt.axis_height_factor[5] = 1

        fplt.show(qt_exec=False)  # prepares plots when they're all setup
        # fplt.refresh()  # refresh autoscaling when all plots complete

    def on_chart_right_drag(self, ev, axis):
        vb = self.axs[0].vb

        p1 = vb.mapToView(ev.pos())
        # p1 = _clamp_point(vb.parent(), p1)

        if not vb.drawing:
            # add new rect
            p0 = vb.mapToView(ev.buttonDownPos())
            # p0 = _clamp_point(vb.parent(), p0)

            r = QRectF(p0, p1)
            vb.draw_rect = fplt.FinRect(ax=self.axs[0], brush=pg.mkBrush('#88888844'), pos=p0, size=r.size(), pen=pg.mkPen(fplt.draw_line_color), movable=True)
            vb.draw_rect.addScaleHandle([0.5, 1], [0.5, 0])  # top
            vb.draw_rect.addScaleHandle([0.5, 0], [0.5, 1])  # down
            vb.draw_rect.addScaleHandle([0, 0.5], [1, 0.5])  # left
            vb.draw_rect.addScaleHandle([1, 0.5], [0, 0.5])  # right
            vb.draw_rect.setZValue(-40)
            vb.rois.append(vb.draw_rect)
            vb.addItem(vb.draw_rect)
            vb.drawing = True
        else:
            r = QRectF(vb.draw_rect.pos(), p1)
            vb.draw_rect.setPos(r.topLeft())
            vb.draw_rect.setSize(r.size(), update=False)
        if ev.isFinish():
            vb.drawing = False
        ev.accept()

    def on_file_open_random_click(self):
        # directory_path = "./data/m15"

        try:
            # disable UI updating
            self.setUpdatesEnabled(False)
            self.blockSignals(True)

            symbols = ["BTC", "ETH", "LTC", "XRP"]
            symbol = symbols[random.randint(0, len(symbols)-1)]

            dt_start = utils.str_to_datetime('2019-10-01T00:00:00') + timedelta(days=random.randint(1, 365*5))
            dt_end = dt_start + timedelta(days=30)

            timeframe = 'm15'
            timeframe_in_secs = utils.timeframe_text_to_seconds(timeframe)

            str_url = f'https://www.bitstamp.net/api-internal/tradeview/price-history/{symbol}/USD/?step={timeframe_in_secs}&start_datetime={utils.datetime_to_str(dt_start)}&end_datetime={utils.datetime_to_str(dt_end)}'
            print(f"on_file_open_random_click: url={str_url}")
            r = requests.get(str_url)

            df = pd.DataFrame(r.json()['data']).astype({'timestamp': int, 'open': float, 'close': float, 'high': float, 'low': float, 'volume': float})

            # fix duplicated data (data from exchange has duplicated values on timestamp
            df = df.drop_duplicates(subset=['timestamp'])
            df.reset_index(drop=True, inplace=True)

            df['time'] = df['timestamp'] * 1000
            self.df_full = df[['time', 'open', 'close', 'high', 'low', 'volume']]

            self.load_data()

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # enable UI updating
            self.setUpdatesEnabled(True)
            self.blockSignals(False)

    def reset_data(self):
        for ax in self.axs:
            ax.reset()
        self.axo.reset()
        df = pd.DataFrame([])

    def load_data(self):
        self.reset_data()

        self.df_full = self.df_full.astype({'time': 'datetime64[ms]', 'open': float, 'high': float, 'low': float, 'close': float, 'volume': float})
        self.df_full['time'] = self.df_full['time'].dt.tz_localize(None)

        # make date shift randomly
        self.df_full['time'] = self.df_full['time'] - pd.Timedelta(days=random.randint(1, 365*10))

        # make price scale randomly
        # also fix the bug of finplot which cannot display with small values (less than 1)
        avg_open = self.df_full['open'].mean()
        random_min = 0.1 if avg_open > 1 else 10
        random_max = 10 if avg_open > 1 else 1000

        random_float = random.uniform(random_min, random_max)
        self.df_full['open'] = self.df_full['open'] * random_float
        self.df_full['high'] = self.df_full['high'] * random_float
        self.df_full['low'] = self.df_full['low'] * random_float
        self.df_full['close'] = self.df_full['close'] * random_float

        self.df = self.df_full[:100].copy()  # get first 100 bars
        self.playback_state.index = 100

        # create candle
        self.candles = fplt.candlestick_ochl(self.df[['time', 'open', 'close', 'high', 'low', 'volume']], ax=self.axs[0])
        fplt.refresh()

        self.on_play_next()  # play init

    def on_play_next(self):
        index = self.playback_state.index
        df_size = len(self.df_full)

        self.lbl_status_bar_msg.setText(f"Bar: {index}/{df_size}")

        if index >= df_size - 1:
            print("on_play_next: End of File!")
            return

        new_row = self.df_full.iloc[index]
        self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
        self.candles.update_data(self.df, gfx=False)
        self.candles.update_gfx()
        self.playback_state.index = index + 1

        self.update_trade_info()
        self.update_entry_line()

    def update_trade_info(self):
        self.lbl_account_balance.setText(f"Balance:  {self.trade_state.balance}")
        self.lbl_trade.setText(f"Trade: {self.trade_state.position_state.name}")
        self.lbl_total_trades_count.setText(f"Total Trades Count: {self.total_trades_count}")
        if self.trade_state.position_state == trading.PositionState.FLAT:
            self.lbl_entry.setText("Entry: None")
            self.lbl_position_size.setText("Size: None")
            self.lbl_pnl_unreliable.setText("Unreliable PnL: None")
            # self.lbl_pnl.setText("PnL: None")
        else:
            self.lbl_entry.setText(f"Entry: {self.trade_state.entry_price}")
            self.lbl_position_size.setText(f"Size: {self.trade_state.position_size}")

            islong = self.trade_state.position_state == trading.PositionState.LONG
            pnl_unreliable_percentage = utils.get_pnl_percent(self.trade_state.entry_price, self.df.iloc[-1]["close"], islong)
            pnl_unreliable = pnl_unreliable_percentage * self.trade_state.position_size / 100
            self.lbl_pnl_unreliable.setText(f"Unreliable PnL: {pnl_unreliable} ({pnl_unreliable_percentage}%)")
            # self.lbl_pnl.setText("PnL: 0")

            if self.trade_state.balance + pnl_unreliable < 0:  # liquidated!
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.setText("Your account is gone!.")
                msg_box.setWindowTitle("Liquidated!")
                msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg_box.exec()


    def on_btn_market_long_clicked(self):
        if self.trade_state.position_state == trading.PositionState.FLAT:
            self.trade_state.position_state = trading.PositionState.LONG
            self.trade_state.entry_price = self.df.iloc[-1]["close"]
            self.trade_state.position_size = self.trade_state.balance
            self.update_trade_info()
            self.update_entry_line()
        elif self.trade_state.position_state == trading.PositionState.LONG:  # DCA
            order_size = self.trade_state.balance
            self.trade_state.entry_price = utils.get_entry_price_adding_to_position(self.trade_state.position_size, self.trade_state.entry_price, self.trade_state.balance, self.df.iloc[-1]["close"])
            self.trade_state.position_size += order_size
            self.update_trade_info()
            self.update_entry_line()

    def update_entry_line(self):
        if self.ref_entry_line is not None:
            fplt.remove_primitive(self.ref_entry_line)

        if self.trade_state.position_state != trading.PositionState.FLAT:
            line_color = '#008000' if self.trade_state.position_state == trading.PositionState.LONG else '#FF0000'
            self.ref_entry_line = fplt.add_line((self.df.iloc[0]['time'], self.trade_state.entry_price), (self.df.iloc[-1]['time'], self.trade_state.entry_price), color=line_color, width=5, style='-', interactive=False, ax=self.axs[0])

    def on_btn_close_trade_clicked(self):
        if self.trade_state.position_state == trading.PositionState.FLAT:
            return

        islong = self.trade_state.position_state == trading.PositionState.LONG
        pnl_percentage = utils.get_pnl_percent(self.trade_state.entry_price, self.df.iloc[-1]["close"], islong)
        pnl = pnl_percentage * self.trade_state.position_size / 100
        if not pd.isna(pnl):
            self.trade_state.balance += pnl

        self.trade_state.position_state = trading.PositionState.FLAT
        self.trade_state.entry_price = float('NaN')
        self.trade_state.position_size = float(0)

        self.total_trades_count += 1
        self.update_trade_info()
        self.update_entry_line()

    def on_btn_market_short_clicked(self):
        if self.trade_state.position_state == trading.PositionState.FLAT:
            self.trade_state.position_state = trading.PositionState.SHORT
            self.trade_state.entry_price = self.df.iloc[-1]["close"]
            self.trade_state.position_size = self.trade_state.balance
            self.update_trade_info()
            self.update_entry_line()
        elif self.trade_state.position_state == trading.PositionState.SHORT:  # DCA
            order_size = self.trade_state.balance
            self.trade_state.entry_price = utils.get_entry_price_adding_to_position(self.trade_state.position_size, self.trade_state.entry_price, self.trade_state.balance, self.df.iloc[-1]["close"])
            self.trade_state.position_size += order_size
            self.update_trade_info()
            self.update_entry_line()