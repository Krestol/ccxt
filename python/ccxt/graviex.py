# -*- coding: utf-8 -*-


from ccxt.base.exchange import Exchange
import math
import json
from ccxt.base.errors import ExchangeError
from ccxt.base.errors import AuthenticationError
from ccxt.base.errors import ArgumentsRequired
from ccxt.base.errors import InsufficientFunds
from ccxt.base.errors import InvalidAddress
from ccxt.base.errors import InvalidOrder
from ccxt.base.errors import OrderNotFound
from ccxt.base.errors import DDoSProtection
from ccxt.base.errors import ExchangeNotAvailable
from ccxt.base.errors import InvalidNonce
from ccxt.base.decimal_to_precision import ROUND


class graviex(Exchange):

    def describe(self):
        return self.deep_extend(super(graviex, self).describe(), {
            'id': 'graviex',
            'name': 'Graviex',
            'version': 'v3',
            'countries': [ 'MT', 'RU' ], # TODO research what for
            'rateLimit': 1000,
            'has': {
                'createOrder': True,
                'createMarketOrder': False,
                'createLimitOrder': False,
                'createDepositAddress': True,
                'deposit': True,
                # 'fetchCurrencies': True,
                'fetchDepositAddress': True,
                'fetchTickers': True,
                'fetchOHLCV': True,
                'fetchOrder': True,
                'fetchBalance': True,
                'fetchOpenOrders': True,
                'fetchClosedOrders': True,
                'fetchMyTrades': True,
                'fetchDeposits': True,
                'fetchWithdrawals': True,
                'fetchTransactions': False,
                'withdraw': False,
            },
            'timeframes': {
                '1m': '1',
                '5m': '5',
                '15m': '15',
                '30m': '30',
                '1h': '60',
                '2h': '120',
                '4h': '240',
                '6h': '360',
                '12h': '720',
                '1d': '1440',
                '3d': '4320',
                '1w': '10080',
            },
            'urls': {
                'logo': '',
                'api': {
                    'public': 'https://graviex.net/api',
                    'private': 'https://graviex.net/api',
                },
                'www': 'https://graviex.net',
                'doc': 'https://graviex.net/documents/api_v3',
                'fees': 'https://graviex.net/documents/fees-and-discounts',
            },
            'api': {
                'public': {
                    'get': [
                        'markets',
                        'tickers',
                        'order_book',
                        'depth',
                        'trades',
                        'trades_simple',
                        'k',
                        'k_with_pending_trades',
                        'currency/info',
                        'timestamp',
                    ],
                },
                'private': {
                    'get': [
                        'account/history',
                        'members/me',
                        'deposits',
                        'deposit',
                        'deposit_address',
                        'fund_sources',
                        'gen_deposit_address',
                        'withdraws',
                        'orders',
                        'orders/history',
                        'order',
                        'trades/my',
                        'trades/history',
                        'settings/get',
                        'strategies/list',
                        'strategies/my',
                    ],
                    'post': [
                        'create_fund_source',
                        'remove_fund_source',
                        'members/me/register_device',
                        'members/me/update_preferences',
                        'orders',
                        'orders/multi',
                        'orders/clear',
                        'order/delete',
                        'create_withdraw',
                        'settings/store',
                        'strategy/cancel',
                        'strategy/create',
                        'strategy/update',
                        'strategy/activate',
                        'strategy/deactivate',
                    ],
                },
            },
            'fees': {
                'trading': {
                    'percentage': True,
                    'maker': 0.0,
                    'taker': 0.2 / 100,
                },
                'funding': {
                    'withdraw': {
                        'BTC': 0.0004,
                        'ETH': 0.0055,
                        'DOGE': 2.0,
                        'NYC': 1.0,
                        'XMR': 0.02,
                        'PIVX': 0.2,
                        'NEM': 0.05,
                        'SCAVO': 5.0,
                        'SEDO': 5.0,
                        'USDT': 3.0,
                        'GDM': 0.3,
                        'PIRL': 0.005,
                        'PK': 0.1,
                        'ORM': 10,
                        'NCP': 10,
                        'ETM': 10,
                        'USD': 0,
                        'EUR': 0,
                        'RUB': 0,
                        'other': 0.002,
                    },
                },
            },
            'limits': {
                'amount': {
                    'min': 0.001,
                    'max': None,
                },
            },
            'precision': {
                'amount': 8,
                'price': 8,
            },
        })

    def nonce(self):
        return self.seconds()

    # def fetch_time(self, params={}):
    #     response = self.publicGetTime(params)
    #     return self.safe_float(response, 'serverTime')

    # def load_time_difference(self):
    #     serverTime = self.fetch_time()
    #     after = self.milliseconds()
    #     self.options['timeDifference'] = int(after - serverTime)
    #     return self.options['timeDifference']

    def fetch_markets(self, params={}):
        response = self.publicGetTickers(params)
        # ids = response.keys()
        result = []
        for id in response:
            
            # id = ids[i]
            market = response[id]
            api = self.safe_value (market, 'api')
            wstatus = self.safe_string (market, 'wstatus')
            active = False

            if api == True and wstatus == 'on':
                active = True
            minamount = self.safe_float(market, 'base_min')
            baseId = self.safe_string(market, 'base_unit').upper()
            quoteId = self.safe_string(market, 'quote_unit').upper()
            base = self.safe_currency_code(baseId)
            quote = self.safe_currency_code(quoteId)
            symbol = self.safe_string(market, 'name')
            if 'GIO/BTC' == symbol:
                print(market)

            result.append(self.extend(self.fees['trading'], {
                'info': market,
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'baseId': baseId,
                'quoteId': quoteId,
                'active': active,
                'taker': None,
                'maker': None,
                'limits': {
                    'amount': {
                        'min': minamount,
                        'max': None,
                    },
                },
            }))
        return result

    # def calculate_fee(self, symbol, type, side, amount, price, takerOrMaker='taker', params={}):
    #     market = self.markets[symbol]
    #     key = 'quote'
    #     rate = market[takerOrMaker]
    #     cost = amount * rate
    #     precision = market['precision']['price']
    #     if side == 'sell':
    #         cost *= price
    #     else:
    #         key = 'base'
    #         precision = market['precision']['amount']
    #     cost = self.decimal_to_precision(cost, ROUND, precision, self.precisionMode)
    #     return {
    #         'type': takerOrMaker,
    #         'currency': market[key],
    #         'rate': rate,
    #         'cost': float(cost),
    #     }

    def fetch_balance(self, params={}):
        self.load_markets()
        response = self.privateGetMembersMe()
        result = {'info': response}
        balances = response['accounts_filtered']
        for i in range(0, len(balances)):
            balance = balances[i]
            currencyId = self.safe_string(balance, 'currency').upper()
            currency = None
            if currencyId in self.currencies_by_id:
                currency = self.currencies_by_id[currencyId]['code']
            else:
                currency = self.common_currency_code(currencyId)
            free = self.safe_float(balance, 'balance')
            used = self.safe_float(balance, 'locked')
            total = self.sum(free, used)
            result[currency] = {
                'free': free,
                'used': used,
                'total': total,
            }

        return self.parse_balance(result)

    def fetch_order_book(self, symbol, limit=None, params={}):
        self.load_markets()

        if limit is None:
            limit = 20

        request = {
            'market': self.market_id (symbol),
            'limit': limit,
        }
        response = self.publicGetDepth (self.extend (request, params))
        return self.parse_order_book(response)        

    def parse_ticker(self, ticker, market=None):
        timestamp = self.safe_integer(ticker, 'at')
        symbol = self.safe_string(market, 'symbol')
        if timestamp is not None:
            timestamp = timestamp * 1000
        info = ticker
        lastPrice = self.safe_float (ticker, 'last')
        openPrice = self.safe_float (ticker, 'open')
        percentage = None
        average = None
        change = None
        if lastPrice is not None and openPrice is not None:
            change = lastPrice - openPrice
            if openPrice > 0 and change > 0:
                percentage = change / openPrice * 100
            average = self.sum(openPrice, lastPrice) / 2
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': self.safe_float(ticker, 'high'),
            'low': self.safe_float(ticker, 'low'),
            'bid': self.safe_float(ticker, 'buy'),
            'bidVolume': None,
            'ask': self.safe_float(ticker, 'sell'),
            'askVolume': None,
            'vwap': None,
            'open': openPrice,
            'close': lastPrice,
            'last': lastPrice,
            'previousClose': None,
            'change': change,
            'percentage': percentage,
            'average': average,
            'baseVolume': self.safe_float (ticker, 'volume'),
            'quoteVolume': self.safe_float (ticker, 'volume2'),
            'info': info,
        }

    # def fetch_status(self, params={}):
    #     response = self.wapiGetSystemStatus()
    #     status = self.safe_value(response, 'status')
    #     if status is not None:
    #         status = 'ok' if (status == 0) else 'maintenance'
    #         self.status = self.extend(self.status, {
    #             'status': status,
    #             'updated': self.milliseconds(),
    #         })
    #     return self.status

    def fetch_ticker(self, symbol, params={}):
        self.load_markets()
        symbols = { symbol}
        return self.fetch_tickers(symbols, params)

    # def parse_tickers(self, rawTickers, symbols=None):
    #     tickers = []
    #     for i in range(0, len(rawTickers)):
    #         tickers.append(self.parse_ticker(rawTickers[i]))
    #     return self.filter_by_array(tickers, 'symbol', symbols)

    # def fetch_bids_asks(self, symbols=None, params={}):
    #     self.load_markets()
    #     response = self.publicGetTickerBookTicker(params)
    #     return self.parse_tickers(response, symbols)

    def fetch_tickers(self, symbols=None, params={}):
        self.load_markets()
        response = self.publicGetTickers(params)
        result = {}
        for id in response:
            market = self.markets_by_id[id]
            symbol = market['symbol']
            result[symbol] = self.parse_ticker(response[id], market)

        if symbols is not None:
            symresult = {}
            for symbol in symbols:
                ticker = self.safe_value(result, symbol)
                if ticker is not None:
                    return ticker
                else:
                    symresult[symbol] = ticker
            return symresult

        return result

    def parse_ohlcv(self, ohlcv, market=None, timeframe='5m', since=None, limit=None):
        return [
            ohlcv[0] * 1000,
            float(ohlcv[1]),
            float(ohlcv[2]),
            float(ohlcv[3]),
            float(ohlcv[4]),
            float(ohlcv[5]),
        ]

    def fetch_ohlcv(self, symbol, timeframe='5m', since=None, limit=None, params={}):
        self.load_markets()
        market = self.market(symbol)

        if limit is None:
            limit = 20

        request = {
            'market': market['id'],
            'period': self.timeframes[timeframe],
            'limit': limit
        }

        if since is not None:
            if since > 9999999999:
                since = int (since / 1000)
            request['timestamp'] = since

        response = self.publicGetK(self.extend(request, params))        
        return self.parse_ohlcvs(response, market, timeframe, since, limit)

    def parse_trade(self, trade, market=None):
        timestamp = self.safe_integer(trade, 'at')
        if timestamp is not None:
            timestamp *= 1000

        price = self.safe_float(trade, 'price')
        amount = self.safe_float(trade, 'volume')
        marketId = self.safe_string(trade, 'market')
        symbol = None if market is None else market['symbol']
        cost = self.cost_to_precision(symbol, price * amount)  

        return {
            'info': trade,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': symbol,
            'id': self.safe_string(trade, 'id'),
            'order': self.safe_string(trade, 'order_id'),
            'type': None,
            'side': self.safe_string(trade, 'side'),
            'takerOrMaker': None,
            'price': price,
            'amount': amount,
            'cost': cost,
            'fee': None,
        }

    def fetch_trades(self, symbol, since=None, limit=None, params={}):
        self.load_markets()
        market = self.market(symbol)
        if limit is None:
            limit = 20
        response = self.publicGetTrades (self.extend ({
                'market': market['id'],
                'limit': limit,
            }, params))
        return self.parse_trades(response, market, since, limit)

    def parse_order_status(self, status):
        statuses = {
            'wait': 'open',
            'done': 'closed',
            'cancel': 'canceled',
        }
        if status in statuses:
            return statuses[status]        
        return status

    def parse_order(self, order, market=None):
        timestamp = self.safe_integer (order, 'at')
        if timestamp is not None:
            timestamp = int(timestamp * 1000)

        symbol = None
        marketId = self.safe_string (order, 'market')
        market = self.safe_value(self.markets_by_id, marketId)
        feeCurrency = None
        if market is not None:
            symbol = market['symbol']
            feeCurrency = market['quote']

        return {
            'id': self.safe_string (order, 'id'),
            'datetime': self.iso8601 (timestamp),
            'timestamp': timestamp,
            'lastTradeTimestamp': None,
            'status': self.parse_order_status(self.safe_string (order, 'state')),
            'symbol': symbol,
            'type': self.safe_string(order, 'ord_type'),
            'side': self.safe_string(order, 'side'),
            'price': self.safe_float(order, 'price'),
            'cost': None,
            'average': self.safe_float(order, 'avg_price'),
            'amount': self.safe_float(order, 'volume'),
            'filled': self.safe_float(order, 'executed_volume'),
            'remaining': self.safe_float(order, 'remaining_volume'),
            'trades': self.safe_integer(order, 'trades_count'),
            'fee': {
                'currency': feeCurrency,
                'cost': None,
            },
            'info': order,
        }
        

    def create_order(self, symbol, ordType, side, amount, price=None, params={}):
        self.load_markets()
        market = self.market(symbol)
        request = {
            'market': market['id'],
            'volume': self.amount_to_precision(symbol, amount),
            'side': side,
        }

        if price is not None:
            request['price'] = price
        if ordType is not None:
            request['ord_type'] = ordType

        response = self.privatePostOrders(self.extend(request, params))
        order = self.parse_order(response, market)
        id = self.safe_string(order, 'id')
        self.orders[id] = order
        return order

    def fetch_order(self, id, symbol=None, params={}):        
        self.load_markets()
        market = self.market(symbol)
        origClientOrderId = self.safe_value(params, 'origClientOrderId')
        request = {
            'id': id,
        }        
        response = self.privateGetOrder(self.extend(request, params))
        return self.parse_order(response, market)

    # def fetch_orders(self, symbol=None, since=None, limit=None, params={}):
    #     if symbol is None:
    #         raise ArgumentsRequired(self.id + ' fetchOrders requires a symbol argument')
    #     self.load_markets()
    #     market = self.market(symbol)
    #     request = {
    #         'symbol': market['id'],
    #     }
    #     if since is not None:
    #         request['startTime'] = since
    #     if limit is not None:
    #         request['limit'] = limit
    #     response = self.privateGetAllOrders(self.extend(request, params))
    #     #
    #     #     [
    #     #         {
    #     #             "symbol": "LTCBTC",
    #     #             "orderId": 1,
    #     #             "clientOrderId": "myOrder1",
    #     #             "price": "0.1",
    #     #             "origQty": "1.0",
    #     #             "executedQty": "0.0",
    #     #             "cummulativeQuoteQty": "0.0",
    #     #             "status": "NEW",
    #     #             "timeInForce": "GTC",
    #     #             "type": "LIMIT",
    #     #             "side": "BUY",
    #     #             "stopPrice": "0.0",
    #     #             "icebergQty": "0.0",
    #     #             "time": 1499827319559,
    #     #             "updateTime": 1499827319559,
    #     #             "isWorking": True
    #     #         }
    #     #     ]
    #     #
    #     return self.parse_orders(response, market, since, limit)

    def parse_order_status_re(self, status):
        statuses = {
            'open': 'wait',
            'closed': 'done',
            'canceled': 'cancel',
        }
        if status in statuses:
            return statuses[status]
        
        return status

    def fetch_orders_by_status(self, status, symbol = None, since = None, limit = None, params = {}):
        self.load_markets()        
        pstatus = self.parse_order_status_re(status)

        if limit is None:
            limit = 100
        
        request = {
            'page': 1,
            'limit': limit,
            'state': pstatus,
        }

        market = None
        if symbol is not None:
            market = self.market(symbol)
            request['market'] = market['id']

        response = self.privateGetOrders(self.extend(request, params))
        return self.parse_orders(response, market, since, limit)

    def fetch_open_orders(self, symbol=None, since=None, limit=None, params={}):
        return self.fetch_orders_by_status('open', symbol, since, limit, params)

    def fetch_orders_by_status(self, status, symbol = None, since = None, limit = None, params = {}):
        self.load_markets()
        pstatus = self.parse_order_status_re(status)
        if limit is None:
            limit = 100

        request = {
            'page': 1,
            'limit': limit,
            'state': pstatus,
        }

        market = None

        if symbol is not None:
            market = self.market(symbol)
            request['market'] = market['id']

        response = self.privateGetOrders(self.extend(request, params))
        return self.parse_orders(response, market, since, limit)

    def fetch_closed_orders(self, symbol=None, since=None, limit=None, params={}):
        return self.fetch_orders_by_status('closed', symbol, since, limit, params)

    def cancel_order(self, id, symbol=None, params={}):
        self.privatePostOrderDelete(self.extend({
            'id': id,
        }, params))
        return self.fetch_order(id, symbol)

    def fetch_my_trades(self, symbol=None, since=None, limit=None, params={}):
        self.load_markets()
        if limit is None:
            limit = 100

        request = {
            'limit': limit,
        }
        market = None
        if symbol is not None:
            market = self.market(symbol)
            request['market'] = market['id']

        response = self.privateGetTradesMy(self.extend(request, params))
        return self.parse_trades(response, market, since, limit)

    # def fetch_my_dust_trades(self, symbol=None, since=None, limit=None, params={}):
    #     #
    #     # Bianance provides an opportunity to trade insignificant(i.e. non-tradable and non-withdrawable)
    #     # token leftovers(of any asset) into `BNB` coin which in turn can be used to pay trading fees with it.
    #     # The corresponding trades history is called the `Dust Log` and can be requested via the following end-point:
    #     # https://github.com/binance-exchange/binance-official-api-docs/blob/master/wapi-api.md#dustlog-user_data
    #     #
    #     self.load_markets()
    #     response = self.wapiGetUserAssetDribbletLog(params)
    #     # {success:    True,
    #     #   results: {total:    1,
    #     #               rows: [{    transfered_total: "1.06468458",
    #     #                         service_charge_total: "0.02172826",
    #     #                                      tran_id: 2701371634,
    #     #                                         logs: [{             tranId:  2701371634,
    #     #                                                   serviceChargeAmount: "0.00012819",
    #     #                                                                   uid: "35103861",
    #     #                                                                amount: "0.8012",
    #     #                                                           operateTime: "2018-10-07 17:56:07",
    #     #                                                      transferedAmount: "0.00628141",
    #     #                                                             fromAsset: "ADA"                  }],
    #     #                                 operate_time: "2018-10-07 17:56:06"                                }]} }
    #     results = self.safe_value(response, 'results', {})
    #     rows = self.safe_value(results, 'rows', [])
    #     data = []
    #     for i in range(0, len(rows)):
    #         logs = rows[i]['logs']
    #         for j in range(0, len(logs)):
    #             logs[j]['isDustTrade'] = True
    #             data.append(logs[j])
    #     trades = self.parse_trades(data, None, since, limit)
    #     return self.filter_by_since_limit(trades, since, limit)

    # def parse_dust_trade(self, trade, market=None):
    #     # {             tranId:  2701371634,
    #     #   serviceChargeAmount: "0.00012819",
    #     #                   uid: "35103861",
    #     #                amount: "0.8012",
    #     #           operateTime: "2018-10-07 17:56:07",
    #     #      transferedAmount: "0.00628141",
    #     #             fromAsset: "ADA"                  },
    #     orderId = self.safe_string(trade, 'tranId')
    #     timestamp = self.parse8601(self.safe_string(trade, 'operateTime'))
    #     tradedCurrency = self.safe_currency_code(self.safe_string(trade, 'fromAsset'))
    #     earnedCurrency = self.currency('BNB')['code']
    #     applicantSymbol = earnedCurrency + '/' + tradedCurrency
    #     tradedCurrencyIsQuote = False
    #     if applicantSymbol in self.markets:
    #         tradedCurrencyIsQuote = True
    #     #
    #     # Warning
    #     # Binance dust trade `fee` is already excluded from the `BNB` earning reported in the `Dust Log`.
    #     # So the parser should either set the `fee.cost` to `0` or add it on top of the earned
    #     # BNB `amount`(or `cost` depending on the trade `side`). The second of the above options
    #     # is much more illustrative and therefore preferable.
    #     #
    #     fee = {
    #         'currency': earnedCurrency,
    #         'cost': self.safe_float(trade, 'serviceChargeAmount'),
    #     }
    #     symbol = None
    #     amount = None
    #     cost = None
    #     side = None
    #     if tradedCurrencyIsQuote:
    #         symbol = applicantSymbol
    #         amount = self.sum(self.safe_float(trade, 'transferedAmount'), fee['cost'])
    #         cost = self.safe_float(trade, 'amount')
    #         side = 'buy'
    #     else:
    #         symbol = tradedCurrency + '/' + earnedCurrency
    #         amount = self.safe_float(trade, 'amount')
    #         cost = self.sum(self.safe_float(trade, 'transferedAmount'), fee['cost'])
    #         side = 'sell'
    #     price = None
    #     if cost is not None:
    #         if amount:
    #             price = cost / amount
    #     id = None
    #     type = None
    #     takerOrMaker = None
    #     return {
    #         'id': id,
    #         'timestamp': timestamp,
    #         'datetime': self.iso8601(timestamp),
    #         'symbol': symbol,
    #         'order': orderId,
    #         'type': type,
    #         'takerOrMaker': takerOrMaker,
    #         'side': side,
    #         'amount': amount,
    #         'price': price,
    #         'cost': cost,
    #         'fee': fee,
    #         'info': trade,
    #     }

    # def fetch_deposits(self, code=None, since=None, limit=None, params={}):
    #     self.load_markets()
    #     currency = None
    #     request = {}
    #     if code is not None:
    #         currency = self.currency(code)
    #         request['asset'] = currency['id']
    #     if since is not None:
    #         request['startTime'] = since
    #     response = self.wapiGetDepositHistory(self.extend(request, params))
    #     #
    #     #     {    success:    True,
    #     #       depositList: [{insertTime:  1517425007000,
    #     #                            amount:  0.3,
    #     #                           address: "0x0123456789abcdef",
    #     #                        addressTag: "",
    #     #                              txId: "0x0123456789abcdef",
    #     #                             asset: "ETH",
    #     #                            status:  1                                                                    }]}
    #     #
    #     return self.parse_transactions(response['depositList'], currency, since, limit)

    # def fetch_withdrawals(self, code=None, since=None, limit=None, params={}):
    #     self.load_markets()
    #     currency = None
    #     request = {}
    #     if code is not None:
    #         currency = self.currency(code)
    #         request['asset'] = currency['id']
    #     if since is not None:
    #         request['startTime'] = since
    #     response = self.wapiGetWithdrawHistory(self.extend(request, params))
    #     #
    #     #     {withdrawList: [{     amount:  14,
    #     #                             address: "0x0123456789abcdef...",
    #     #                         successTime:  1514489710000,
    #     #                          addressTag: "",
    #     #                                txId: "0x0123456789abcdef...",
    #     #                                  id: "0123456789abcdef...",
    #     #                               asset: "ETH",
    #     #                           applyTime:  1514488724000,
    #     #                              status:  6                       },
    #     #                       {     amount:  7600,
    #     #                             address: "0x0123456789abcdef...",
    #     #                         successTime:  1515323226000,
    #     #                          addressTag: "",
    #     #                                txId: "0x0123456789abcdef...",
    #     #                                  id: "0123456789abcdef...",
    #     #                               asset: "ICN",
    #     #                           applyTime:  1515322539000,
    #     #                              status:  6                       }  ],
    #     #            success:    True                                         }
    #     #
    #     return self.parse_transactions(response['withdrawList'], currency, since, limit)

    # def parse_transaction_status_by_type(self, status, type=None):
    #     if type is None:
    #         return status
    #     statuses = {
    #         'deposit': {
    #             '0': 'pending',
    #             '1': 'ok',
    #         },
    #         'withdrawal': {
    #             '0': 'pending',  # Email Sent
    #             '1': 'canceled',  # Cancelled(different from 1 = ok in deposits)
    #             '2': 'pending',  # Awaiting Approval
    #             '3': 'failed',  # Rejected
    #             '4': 'pending',  # Processing
    #             '5': 'failed',  # Failure
    #             '6': 'ok',  # Completed
    #         },
    #     }
    #     return statuses[type][status] if (status in statuses[type]) else status

    # def parse_transaction(self, transaction, currency=None):
    #     #
    #     # fetchDeposits
    #     #      {insertTime:  1517425007000,
    #     #            amount:  0.3,
    #     #           address: "0x0123456789abcdef",
    #     #        addressTag: "",
    #     #              txId: "0x0123456789abcdef",
    #     #             asset: "ETH",
    #     #            status:  1                                                                    }
    #     #
    #     # fetchWithdrawals
    #     #
    #     #       {     amount:  14,
    #     #             address: "0x0123456789abcdef...",
    #     #         successTime:  1514489710000,
    #     #          addressTag: "",
    #     #                txId: "0x0123456789abcdef...",
    #     #                  id: "0123456789abcdef...",
    #     #               asset: "ETH",
    #     #           applyTime:  1514488724000,
    #     #              status:  6                       }
    #     #
    #     id = self.safe_string(transaction, 'id')
    #     address = self.safe_string(transaction, 'address')
    #     tag = self.safe_string(transaction, 'addressTag')  # set but unused
    #     if tag is not None:
    #         if len(tag) < 1:
    #             tag = None
    #     txid = self.safe_value(transaction, 'txId')
    #     currencyId = self.safe_string(transaction, 'asset')
    #     code = self.safe_currency_code(currencyId, currency)
    #     timestamp = None
    #     insertTime = self.safe_integer(transaction, 'insertTime')
    #     applyTime = self.safe_integer(transaction, 'applyTime')
    #     type = self.safe_string(transaction, 'type')
    #     if type is None:
    #         if (insertTime is not None) and (applyTime is None):
    #             type = 'deposit'
    #             timestamp = insertTime
    #         elif (insertTime is None) and (applyTime is not None):
    #             type = 'withdrawal'
    #             timestamp = applyTime
    #     status = self.parse_transaction_status_by_type(self.safe_string(transaction, 'status'), type)
    #     amount = self.safe_float(transaction, 'amount')
    #     return {
    #         'info': transaction,
    #         'id': id,
    #         'txid': txid,
    #         'timestamp': timestamp,
    #         'datetime': self.iso8601(timestamp),
    #         'address': address,
    #         'tag': tag,
    #         'type': type,
    #         'amount': amount,
    #         'currency': code,
    #         'status': status,
    #         'updated': None,
    #         'fee': None,
    #     }

    def fetch_deposit_address(self, code, params={}):
        response = self.privateGetDepositAddress(self.extend ({
            'currency': code.lower(),
        }, params))

        address = json.loads(response)
        address = json.loads(address)
        self.check_address(address)

        return {
            'currency': code,
            'address': self.check_address(address),
            'tag': None,
            'info': response,
        }

    def create_deposit_address(self, code, params = {}):
        response = self.privateGetGenDepositAddress(self.extend({
            'currency': code.lower(),
        }, params))

        response = json.loads(response)
        return response

    # def fetch_funding_fees(self, codes=None, params={}):
    #     response = self.wapiGetAssetDetail(params)
    #     #
    #     #     {
    #     #         "success": True,
    #     #         "assetDetail": {
    #     #             "CTR": {
    #     #                 "minWithdrawAmount": "70.00000000",  #min withdraw amount
    #     #                 "depositStatus": False,//deposit status
    #     #                 "withdrawFee": 35,  # withdraw fee
    #     #                 "withdrawStatus": True,  #withdraw status
    #     #                 "depositTip": "Delisted, Deposit Suspended"  #reason
    #     #             },
    #     #             "SKY": {
    #     #                 "minWithdrawAmount": "0.02000000",
    #     #                 "depositStatus": True,
    #     #                 "withdrawFee": 0.01,
    #     #                 "withdrawStatus": True
    #     #             }
    #     #         }
    #     #     }
    #     #
    #     detail = self.safe_value(response, 'assetDetail', {})
    #     ids = list(detail.keys())
    #     withdrawFees = {}
    #     for i in range(0, len(ids)):
    #         id = ids[i]
    #         code = self.safe_currency_code(id)
    #         withdrawFees[code] = self.safe_float(detail[id], 'withdrawFee')
    #     return {
    #         'withdraw': withdrawFees,
    #         'deposit': {},
    #         'info': response,
    #     }

    # def withdraw(self, code, amount, address, tag=None, params={}):
    #     self.check_address(address)
    #     self.load_markets()
    #     currency = self.currency(code)
    #     name = address[0:20]
    #     request = {
    #         'asset': currency['id'],
    #         'address': address,
    #         'amount': float(amount),
    #         'name': name,
    #     }
    #     if tag is not None:
    #         request['addressTag'] = tag
    #     response = self.wapiPostWithdraw(self.extend(request, params))
    #     return {
    #         'info': response,
    #         'id': self.safe_string(response, 'id'),
    #     }

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):        
        url = self.urls['api'][api]
        url += '/' + self.version + '/' + path
        tonce = self.nonce() + 10

        if self.apiKey is not None:
            params['access_key'] = self.apiKey

        params['tonce'] = str(tonce) + '000'
        keysort = self.keysort(params)
        
        if api is not 'public':
            signStr = method + '|' + url.replace('https://graviex.net', '') + '|' + self.urlencode(keysort)
            signature = self.hmac(self.encode(signStr), self.encode(self.secret), 'sha256')
            keysort['signature'] = signature
        
        paramEncoded = self.urlencode(keysort)

        if method is 'POST':
            body = paramEncoded
        else:
            url += '?' + paramEncoded

        return {'url': url, 'method': method, 'body': body, 'headers': headers}
        

    def handle_errors(self, code, reason, url, method, headers, body, response, requestHeaders, requestBody):
        msg = 'Unknown error'
        if code == 503 or code == 502:
            raise ExchangeError('Exchange Overloaded')
        
        if response is not None and 'error' in response:
            errorCode = self.safe_integer(response['error'], 'code')
            if errorCode is not None:
                msg = self.safe_string(response['error'], 'message')
                if errorCode == 2002:
                    raise InsufficientFunds(msg)
                if errorCode == 2005 or errorCode is 2007:
                    raise AuthenticationError(msg)
                if errorCode == 1001:
                    raise ExchangeError(msg)

        if code != 200 and code != 201:
            raise ExchangeError('Invalid response from exchange: ' + msg)

        return response