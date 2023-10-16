#!/usr/bin/env python
import time
import traceback
import os
import fire
from trade_screenshots.sip_handler import handle_sip
from trade_screenshots.symbols_handler import handle_symbols
from trade_screenshots.trades_handler import handle_trades


def main(
    start="2023-01-01",  # TODO: start date needed?
    timeframe="1min",  # only allow '<integer>min'
    provider="alpaca-file",
    symbols=None, #"2023-10-02_NVDA",
    # trades_file='trades.csv'
    trades_file=None,
    symbols_file='stocks_in_play.txt',
    trading_hour='09:30-16:00',  # Assume OHLC data is in market time for symbol in question
    filetype="png",
    outdir='images',    
    days=0,
):
    """
    This function generates trade screenshots for a given set of symbols and timeframes.
    :param start: The start date for the trade screenshots. Defaults to "2023-01-01".
    :param timeframe: The timeframe for the trade screenshots. Only allows '<integer>min'. Defaults to "1min".
    :param provider: The provider for the trade data.
    :param symbols: The symbols for which to generate trade screenshots.
    :param trades_file: The file containing the trade data. Defaults to None.
    :param symbols_file: The file containing the symbols for which to generate trade screenshots.
    :param trading_hour: The trading hour for the trade screenshots. Assumes OHLC data is in market time for symbol in question.
    :param filetype: The file type for the generated trade screenshots.
    :param outdir: The output directory for the generated trade screenshots.
    :param days: The number of days for which to generate trade screenshots, 0 for all available data.
    """
        
    if not os.path.exists(outdir):
        raise Exception(f"Output directory '{outdir}' does not exist")
    
    if trading_hour:
        start_time, end_time = trading_hour.split("-")
    else:
        start_time, end_time = None, None
    
    if symbols:
        handle_symbols(start, timeframe, provider, symbols, filetype, outdir, days, start_time, end_time)

    elif trades_file:
        handle_trades(start, timeframe, trades_file, filetype, outdir, days, start_time, end_time)     
    
    elif symbols_file:
        handle_sip(timeframe, symbols_file, filetype, outdir)
    else:
        raise ValueError("symbols, trades_file, or symbols_file must be provided")

if __name__ == "__main__":
    fire.Fire(main)
