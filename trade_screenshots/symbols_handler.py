from concurrent.futures import ProcessPoolExecutor
from functools import partial

import trade_screenshots.plots as plots
import trade_screenshots.utils as utils
from trade_screenshots import utils_ta
from trade_screenshots.common import try_process_symbol


def write_chart(df, timeframe, outdir):    
    symbol = df.attrs['symbol']
    print(f"Creating chart {symbol}: {df.index[0]} - {df.index[-1]}")    
    date = df.index[0]    
    fig  = plots.intraday_chart(df, timeframe, symbol, title=f"{symbol} {date} ({timeframe})")
    filepath =  f"{outdir}/{symbol}-{date.strftime('%Y-%m-%d')}-{timeframe}" if outdir else f"{symbol}-{date.strftime('%Y-%m-%d')}-{timeframe}" 
    utils.write_file(fig, filepath, 'png', 1600, 900)

def create_charts(symbols, start, end, timeframe, provider, outdir, path):
    dfs = []
    for symbol in symbols:
        if provider == 'tv':
            df = utils.get_dataframe_tv(start, timeframe, symbol, path)
        elif provider == 'alpaca-file':
            df = utils.get_dataframe_alpaca(symbol, timeframe, path)
        elif provider == 'alpaca':
            df = utils.download_dataframe_alpaca(start, timeframe, symbol)
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
        if start:        
            df = df.loc[start:]
        if end:        
            df = df.loc[:end]                    
        if df.empty:
            #raise Exception(f"Empty DataFrame for symbol {symbol}")
            print(f"Skipping empty DataFrame for symbol '{symbol}'")
        else:
            dfs.append(df)    

    for df in dfs:
        write_chart(df, timeframe, outdir)


# TODO: use partial decorator ? @functools.partial()
def process_symbol(symbol, start, timeframe, provider, filetype, start_time, end_time, outdir, days, paths, ta_params):
    if provider == 'tv':
        df = utils.get_dataframe_tv(start, timeframe, symbol, paths['tv'])
    elif provider == 'alpaca-file':
        df = utils.get_dataframe_alpaca(symbol, timeframe, paths['alpaca-file'])
    elif provider == 'alpaca':
        df = utils.download_dataframe_alpaca(start, timeframe, symbol)  # TODO: not implemented
    else:
        raise ValueError(f"Unknown provider: {provider}")

    if df.empty:
        raise Exception(f"Empty DataFrame for symbol {symbol}")

    if start != '':
        print(f"{symbol}: filtering df by start date '{start}'")
        df = df.loc[start:]

    print(f"{symbol}: Applying TA to {len(df)} rows")

    # TODO: add mid,vwap, daily/ah/pm levels and store in dataframe as constant values? and write test for it?
    df = utils_ta.add_ta(symbol, df, ['EMA10', 'EMA20', 'EMA50', 'BB'], start_time, end_time)

    print(f"{symbol}: Splitting data into days")
    eth_values = {}
    dfs = utils.split(df, start_time, end_time, eth_values)
    #TODO: days is not needed? (use start instead)
    if days != 0:
        dfs = dfs[-days:]

    print(f"{symbol}: generating images for {len(dfs)} days")
    for i in range(1, len(dfs)):
        today = dfs[i]
        yday = dfs[i - 1]
        date = today.index.date[0]
        levels = {
            'close_1': yday['Close'].iloc[-1],
            'high_1': yday['High'].max(),
            'low_1': yday['Low'].min(),
            'eth_low': eth_values[date]['low'],
            'eth_high': eth_values[date]['high'],
        }

        utils_ta.vwap(today)
        utils_ta.mid(today)

        fig = plots.intraday_chart(
            today,
            timeframe,
            symbol,
            title=f"{symbol} {date} ({timeframe})",
            plot_indicators={key: ta_params[key] for key in ['VWAP', 'EMA10', 'EMA20', 'EMA50', 'BB_UPPER', 'BB_LOWER', 'Mid']},
            or_times=('09:30', '10:30'),
            daily_levels=levels,
        )
        filepath =  f"{outdir}/{symbol}-{date.strftime('%Y-%m-%d')}-{timeframe}" if outdir else f"{symbol}-{date.strftime('%Y-%m-%d')}-{timeframe}" 
        utils.write_file(fig, filepath, filetype, 1600, 900)

    print("done")


def create_charts_day_by_day(start, end, timeframe, provider, symbols, filetype, outdir, days, start_time, end_time, paths, ta_params):
    if isinstance(symbols, tuple):
        symbols = list(symbols)
    elif ',' in symbols:
        symbols = symbols.split(',')
    else:
        symbols = [symbols]
    with ProcessPoolExecutor() as executor:
            # def func(symbol):
            #     try:
            #         return process_symbol(symbol, start=start, timeframe=timeframe, provider=provider, trades=trades, filetype=filetype, start_time=start_time, end_time=end_time, outdir=outdir)
            #     except Exception as e:
            #         print(f"Error processing symbol {symbol}: {e}. Skipping.")
            #         traceback.print_exc()
            #         return None
        func = partial(
                process_symbol, start=start, timeframe=timeframe, provider=provider, filetype=filetype, start_time=start_time, end_time=end_time, outdir=outdir, days=days, paths=paths, ta_params=ta_params
            )
        try_func = partial(try_process_symbol, func)
        results = list(executor.map(try_func, symbols))