# ChatRobot

* **FinanceHelper** telegram bot can give you some advice about which stock to choose or you can just give your own preference. After you confine the stock with several conditions, just affirm your choice. Then you can choose the information by clicking on the corresponding button.

* python3 Dependencies:

  1. rasa_nlu: 

     ~~~
     $ pip install rasa[spacy]
     $ python -m spacy download en_core_web_md
     $ python -m spacy link en_core_web_md en
     ~~~

  2. iexfinance:

     ~~~
     $ pip install iexfinance
     ~~~

  3. sqlite3
  
  4. python-telegram-bot
  
     ~~~
     $ pip install python-telegram-bot
     ~~~

* Usage:

1. enable the telegram robot to handle messages:

~~~
$ python FinanceBot.py
~~~

2. open your telegram and search for **FinanceHelper** bot, then you can access stock Info with the help of this bot.

3. If you don't understand how to access the information, you can send **how to ask** or simply **?**

    to learn how to ask questions.

   