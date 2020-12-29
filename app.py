import pandas as pd
import yfinance as yf
import cufflinks as cf
import dateutil.parser
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import plotly
import plotly.graph_objs as go
import streamlit as st

class StockReturns:
	def __init__(self, symbols):
		self.raw_symbols = symbols
		self.tickers = yf.Tickers(symbols)
		self.symbols = self.tickers.symbols
		if len(self.tickers.symbols) < 2:
			self.tickers = yf.Ticker(symbols)
		else:
			# yfinance does not handle . in symbol properly (for example, 005930.KS)
			has_dot = False
			for symbol in self.tickers.symbols:
				if '.' in symbol:
					has_dot = True
					break
			if has_dot:
				self.tickers = [yf.Ticker(s) for s in self.tickers.symbols]

	@st.cache()
	def history(self, start=None, end=None):
		if start is None:
			start = datetime(datetime.today().year, 1, 2)
		if end is None:
			end = datetime.today()

		if isinstance(self.tickers, list):
			data = [t.history(start=start, end=end) for t in self.tickers]
			return self._merge(self.symbols, data)
		else:
			df = self.tickers.history(start=start, end=end)
		return df

	def _merge(self, symbols, data):
		for i, symbol in enumerate(symbols):
			data[i]['Company'] = symbol

		df = pd.concat(data, axis=0)
		df.index.name = 'Date'
		df = df.reset_index()
		df = df.set_index(['Date', 'Company']).stack().unstack([2,1])
		return df

	def plot(self, start=None, end=None):
		chart = st.empty()
		df = self.history(start, end)

		start, end = st.slider('', value=[start, end], format="YY.MM.DD")
		df = df.query("index >= @start and index <= @end")
		daily_returns = df.asfreq('B', method='bfill')['Close'].pct_change()
		cum_returns = (daily_returns + 1).cumprod()
		cum_returns = cum_returns.fillna(1) * 100 - 100
		fig = cum_returns.iplot(asFigure=True, title='Cumulative Returns')
		chart.plotly_chart(fig, use_container_width=True)


if __name__ == '__main__':
	st.set_page_config(
		page_title="Stock Returns",
		page_icon="💸",
		layout="wide",
		initial_sidebar_state="auto",
	)

	st.sidebar.title('Stock Returns')
	symbols = st.sidebar.text_input('Tickers', 'QQQ ARKK')
	
	period = st.sidebar.selectbox('Select period', ['YTD', '3 Months', '6 Months', '1 Year', '2 Years', '3 Years'])
	if period == 'YTD':
		start = datetime(datetime.today().year, 1, 2).date()
	elif 'Month' in period:
		start = datetime.today() - relativedelta(months=int(period.split(' ')[0]))
	elif 'Year' in period:
		start = datetime.today() - relativedelta(years=int(period.split(' ')[0]))

	start = st.sidebar.date_input('Start Date', start)
	end = st.sidebar.date_input('End Date', datetime.today())

	app = StockReturns(symbols)
	app.plot(start, end)