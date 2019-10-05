#Build companyDB
import sqlite3
import csv
from iexfinance.stocks import Stock
from tqdm import tqdm

with open('companylist.csv','r') as csvfile:
    reader = csv.DictReader(csvfile)
    symbols = [row['Symbol'] for row in reader]
print(len(symbols))
conn = sqlite3.connect('companyDB.db')
c = conn.cursor()
c.execute("DROP TABLE if exists company")
c.execute(
    "CREATE TABLE IF NOT EXISTS company(symbol text COLLATE NOCASE, companyName text　COLLATE NOCASE, exchange text　COLLATE NOCASE, "
    "state text　COLLATE NOCASE, city text　COLLATE NOCASE,country text　COLLATE NOCASE)")

for symbol in tqdm(symbols):
        try:
            stk = Stock(symbol,token="sk_9520be7c9fdb4ae5ad5055d91ce95721")
            res = stk.get_company()
        except:
            continue
        else:
            insert_str = "INSERT INTO company(symbol, companyName, exchange, state, city, country) VALUES(?,?,?,?,?,?)"
            t = tuple([res['symbol'],res['companyName'],res['exchange'],res['state'],res['city'],res['country']])
            c.execute(insert_str, t)
c.execute("commit")