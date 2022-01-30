# capgains-fifo

A simple script to calculate your capital gains from stock purchases and sales using the FIFO method.

It currently doesn't distinguish between funds held more than a year vs less than a year!
Use at your own risk and make sure to review the code before you rely on the results.

## Setup

Install python3 if you haven't already done so. There are no dependencies to install with pip.

## Usage

The tool is rather simple and works by passing a bunch of files to it.
If you have prior year tax lots to factor in you can supply them as an optional argument.
The first mandatory file contains the transactions that will be read in.
The tool is expecting a certain format for that file, you can modify the script to work for a different format.

The other three files should either not exist yet or will be overwritten by the tool.
They will store the dividends, the sales and the remaining lots for next year as csv files.

```shell
python3 main.py [--old-logs-file prev_lots.csv] transactions.csv dividends.csv sales.csv lots.csv
```
