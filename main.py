import argparse
import csv
from datetime import datetime
from decimal import Decimal

buy_verbs = ['Buy Investments', 'Auto-Rebalance Purchase']
dividend_verbs = ['Reinvested Dividend']
sale_verbs = ['Sell Investments', 'Auto-Rebalance Sale', 'Sale Of Recordkeeping Fee']


class Transaction(object):
    def __init__(self, date, amount, fund, units, tx_type):
        self.date = date
        self.amount = Decimal(amount)
        self.fund = fund
        self.units = Decimal(units)
        self.type = tx_type

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return 'Transaction date: %s amount: %s fund: %s units: %s type: %s' %\
               (self.date, self.amount, self.fund, self.units, self.type)

    def is_buy(self):
        return self.type in buy_verbs

    def is_dividend(self):
        return self.type in dividend_verbs

    def is_sale(self):
        return self.type in sale_verbs

    # splits of passed units, updates self to reflect the change and returns a new transaction
    def split_off(self, split_units):
        if split_units > self.units:
            raise Exception('cannot split off %s units because only have %s units available' %\
                            (split_units, self.units))
        split_amount = round(split_units / self.units * self.amount, 2)
        self.amount -= split_amount
        self.units -= split_units
        return Transaction(self.date, split_amount, self.fund, split_units, self.type)


class Sale(object):
    def __init__(self, fund_name, date_acquired, date_sold):
        self.fund_name = fund_name
        self.date_acquired = date_acquired
        self.date_sold = date_sold
        self.proceeds = Decimal(0)
        self.cost = Decimal(0)
        self.units = Decimal(0)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return 'Sale description: %s date_acquired: %s date_sold: %s proceeds: %s cost: %s gain_loss: %s' %\
               (self.description, self.date_acquired, self.date_sold, self.proceeds, self.cost, self.gain_loss)

    @property
    def description(self):
        return '%s %s' % (self.units, self.fund_name)

    @property
    def gain_loss(self):
        return self.proceeds - self.cost


def create_arg_parser():
    p = argparse.ArgumentParser(description='Calculate Capital Gains')
    p.add_argument('transactions_file')
    p.add_argument('dividends_file')
    p.add_argument('sales_file')
    p.add_argument('lots_file')
    return p


def import_transactions(filename):
    txs = []
    with open(filename) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for tx in reader:
            amount = tx['AMOUNT']
            if amount[0] == '$':
                amount = amount[1:]
            date = datetime.strptime(tx['DATE'], '%m/%d/%Y')
            txs.append(Transaction(date, amount, tx['FUND'], tx['UNITS'], tx['TYPE']))
    return txs


def export_sales(filename, sales):
    with open(filename, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['DESCRIPTION', 'DATE ACQUIRED', 'DATE SOLD', 'PROCEEDS', 'COST', 'GAIN/LOSS'])
        for sale in sales:
            writer.writerow([
                sale.description,
                sale.date_acquired.strftime('%m/%d/%Y'),
                sale.date_sold.strftime('%m/%d/%Y'),
                sale.proceeds,
                sale.cost,
                sale.gain_loss
            ])


def export_transactions(filename, txs):
    with open(filename, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['DATE', 'AMOUNT', 'FUND', 'UNITS', 'TYPE'])
        for tx in txs:
            writer.writerow([
                tx.date.strftime('%m/%d/%Y'),
                tx.amount,
                tx.fund,
                tx.units,
                tx.type,
            ])


def filter_dividends(txs):
    return filter(lambda tx: tx.is_dividend(), txs)


def calculate_dividends(txs):
    return sum(amount for amount in map(lambda tx: tx.amount, txs))


def calculate_sales(tx, lots):
    new_sales = []
    while tx.amount > Decimal(0):
        if tx.units >= lots[0].units:
            tx_chunk = tx.split_off(lots[0].units)
            lot = lots.pop(0)
        else:
            tx_chunk = tx.split_off(tx.units)
            lot = lots[0].split_off(tx_chunk.units)

        sale = Sale(tx_chunk.fund, lot.date, tx_chunk.date)
        sale.proceeds = tx_chunk.amount
        sale.cost = lot.amount
        sale.units = lot.units
        new_sales.append(sale)
    return new_sales


def calculate_gains(txs):
    lots = {}
    sales = []
    for tx in txs:
        if tx.is_buy() or tx.is_dividend():
            if tx.fund not in lots:
                lots[tx.fund] = []
            lots[tx.fund].append(tx)
        elif tx.is_sale():
            sales += calculate_sales(tx, lots[tx.fund])
        else:
            raise Exception('Unknown tx type: %s' % tx.type)

    sorted_lots = sum([v for _, v in lots.items()], [])
    sorted_lots.sort(key=lambda lot: lot.date)
    return sales, sorted_lots


if __name__ == '__main__':
    parser = create_arg_parser()
    args = parser.parse_args()
    transactions = import_transactions(args.transactions_file)
    transactions.sort(key=lambda tx: tx.date)
    dividends = list(filter_dividends(transactions))
    dividends_total = calculate_dividends(dividends)
    sales, lots = calculate_gains(transactions)

    print('Dividends: $%s' % dividends_total)
    export_transactions(args.dividends_file, dividends)
    export_sales(args.sales_file, sales)
    export_transactions(args.lots_file, lots)
