#!/usr/bin/env python
# -*- coding: utf-8 -*-
from rasa_nlu.training_data import load_data
from rasa_nlu.config import RasaNLUModelConfig
from rasa_nlu.model import Trainer
from rasa_nlu import config
import re
import random
import sqlite3
from iexfinance.data_apis import get_data_points
from iexfinance.stocks import Stock

import logging
from supl import *

from telegram import ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

reply_keyboard = [['address', 'companyName','ZIP','logo'],
                  ['EMPLOYEES', 'EXCHANGE','WEBSITE'],
                  ['PHONE','WEEK52HIGH','WEEK52LOW'],
                  ['latestPrice','avgTotalVolume','news'],
                  ['history_price','sharesOutstanding'],
                  ['restart']]
skip_keyboard = [['skip_email'],['restart']]
restart_keyboard = [['restart']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
skip_markup = ReplyKeyboardMarkup(skip_keyboard, one_time_keyboard=True)
restart_markup = ReplyKeyboardMarkup(restart_keyboard, one_time_keyboard=True)

interpreter = None
# Create a trainer that uses this config
trainer = Trainer(config.load("config_spacy.yml"))
# Load the training data
training_data = load_data('rasa-stock.json')
# Create an interpreter by training the model
interpreter = trainer.train(training_data)
responses = [
    "Sorry, I can't find any stock that can comply with your requirement.",
    '{} stock may be a good choice.',
    '{} stock is one choice, and there exist other choices.'
]
INIT, EMAIL, ADVICE, AFFIRMED = range(4)
policy_rules = {
    (INIT, "email"): (EMAIL, "Thank you for your subscription! Let's turn to get some stock Info now.", None),
    (INIT, "skip_email"): (EMAIL, "OK. Let's turn to get some stock Info now.", None),
    (INIT, "choose_stock"): (INIT, "Before your query, maybe you are concerned about more stock news.Perhaps you would be pleased to enter your email address to subscribe IEX stock news or simply click on 'skip_email'.", EMAIL),
    (INIT, "ask_stock_advice"):(INIT, "Before your query, maybe you are concerned about more stock news.Perhaps you would be pleased to enter your email address to subscribe IEX stock news or simply click on 'skip_email'.", EMAIL),
    (EMAIL, "choose_stock"):(ADVICE, None, None),
    (EMAIL, "ask_stock_advice"):(ADVICE, None, None),
    (ADVICE, "choose_stock"):(ADVICE, None, None),
    (ADVICE, "ask_stock_advice"):(ADVICE, None, None),
    (ADVICE, "affirm"):(AFFIRMED, "OK. Now you may choose the information you interested in." , None)
}
params,neg_params,suggestions,excluded = {},{},[],[]
state = INIT
pending = None
symbol_file="lookup_tables/symbols.txt"
with open(symbol_file, 'r') as f:
    l=[]
    line = f.readline() # whole line
    line = line[:-1]
    l.append(line)
    while line:
        line = f.readline()
        line = line[:-1]
        if line:
            l.append(line)
    symbols = re.compile('|'.join(l))



# Define find_stocks()
def find_stocks(params, neg_params):
    query = 'SELECT * FROM company'
    if len(params) > 0 and len(neg_params) > 0:
        filters = ["LOWER({})=?".format(k) for k in params] + ["LOWER({})!=?".format(k) for k in neg_params]
        query += " WHERE " + " and ".join(filters)
    elif len(neg_params) > 0:
        filters = ["LOWER({})!=?".format(k) for k in neg_params]
        query += " WHERE " + " and ".join(filters)
    elif len(params) > 0:
        filters = ["LOWER({})=?".format(k) for k in params]
        query += " WHERE " + " and ".join(filters)

    t = tuple(dict(list(params.items()) + list(neg_params.items())).values())
    # open connection to DB
    conn = sqlite3.connect('companyDB.db')
    # create a cursor
    c = conn.cursor()
    # print(query)
    # print(t)
    # print(params)
    # print(neg_params)
    c.execute(query, t)
    return c.fetchall()


def negated_ents(phrase, ent_vals):
    ents = [e for e in ent_vals if e in phrase]
    ends = sorted([phrase.index(e) + len(e) for e in ents])
    start = 0
    chunks = []
    for end in ends:
        chunks.append(phrase[start:end])
        start = end
    result = {}
    for chunk in chunks:
        for ent in ents:
            if ent in chunk:
                if "not" in chunk or "n't" in chunk:
                    result[ent] = False
                else:
                    result[ent] = True
    return result


def interpret(message):
    inter = interpreter.parse(message)
    entities = inter["entities"]
    intent = inter['intent']['name']
    #check whether message contain an email address
    email = re.compile(r'^[A-Za-z0-9\u4e00-\u9fa5]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$')
    if email.search(message):
        intent = 'email'
    return entities, intent


# Define the respond function
def respond(message, params, neg_params, suggestions, excluded):
    # Extract the entities
    entities, intent = interpret(message)

    ent_vals = [e["value"] for e in entities]
    # print(intent)
    # print(entities)
    # Look for negated entities
    negated = negated_ents(message.lower(), ent_vals)

    response = None
    if intent == "deny":
        excluded.extend(suggestions)
        if params.__contains__("symbol"):
            if params['symbol'] in excluded:
                del params['symbol']
    else:
        if intent == "choose_stock":
            params, neg_params = {}, {}
        # confine
        for ent in entities:
            if ent["value"] in negated and not negated[ent["value"]]:
                neg_params[ent["entity"]] = str(ent["value"])
                if params.__contains__(ent["entity"]):
                    del params[ent["entity"]]
            else:
                params[ent["entity"]] = str(ent["value"])
                if neg_params.__contains__(ent["entity"]):
                    del neg_params[ent["entity"]]
        if intent == "choose_stock":
            msg = message.upper()
            if symbols.search(msg) is None or len(entities) == 0:
                response = "Sorry. I can't find the stock　you mentioned."

    if response is not None:
        return response, params, neg_params, suggestions, excluded

    p = find_stocks(params, neg_params)
    # Find the stocks
    results = [r
               for r in p
               if r[0] not in excluded
               ]
    names = [r[0] for r in results]
    n = min(len(results), 2)
    # Return the correct response
    suggestions = names[:1]
    return responses[n].format(*names), params, neg_params, suggestions, excluded


info_list = ['address', 'companyName', 'ZIP', 'logo', 'EMPLOYEES', 'EXCHANGE', 'WEBSITE',
             'PHONE', 'WEEK52HIGH', 'WEEK52LOW', 'latestPrice', 'avgTotalVolume', 'news', 'history_price',
             'sharesOutstanding']


def get_info(message):
    if message in ['address', 'ZIP', 'EMPLOYEES', 'EXCHANGE', 'WEBSITE', 'PHONE', 'WEEK52HIGH', 'WEEK52LOW']:
        return get_data_points(suggestions[0], key=message, token="sk_9520be7c9fdb4ae5ad5055d91ce95721",
                               output_format='pandas')
    else:
        stock = Stock(suggestions[0], token="sk_9520be7c9fdb4ae5ad5055d91ce95721")
        quote = stock.get_quote()
        if message == 'companyName':
            return quote['companyName']
        elif message == 'logo':
            return 'url: ' + stock.get_logo()['url']
        elif message == 'latestPrice':
            return quote['latestPrice']
        elif message == 'avgTotalVolume':
            return quote['avgTotalVolume']
        elif message == 'news':
            news = stock.get_news()
            return '\n'.join(['title: '+n['headline']
                        +'\nurl: '+n['url']
                        for n in news[:5]])
        elif message == 'history_price':
            history_price = stock.get_historical_prices()
            return '\n'.join(['date: '+p['date']
                        +'\nopen: '+str(p['open'])
                        +'\nclose: '+str(p['close'])
                        +'\nhigh: '+str(p['high'])
                        +'\nlow: '+str(p['low'])
                        for p in history_price[-5:]])
        else:  # sharesOutstanding
            return stock.get_key_stats()['sharesOutstanding']


def respond_state(state, pending, message, params, neg_params, suggestions, excluded):
    entities, intent = interpret(message)
    response = None
    if message == 'skip_email':
        intent = 'skip_email'
    if message == 'restart':
        return INIT, None, "Please choose the stock or ask for some recommendation.", {}, {}, [], []
    # intent list ['skip_email','restart','greet','goodbye','ask_stock_advice'
    #  ,'deny','choose_stock','confine' ,'ask_name','affirm','ask_explanation']

    # query info
    if state == AFFIRMED and message in info_list:
        response = get_info(message)
        if type(response) != 'str':
            response = str(response)
        response = message + ':\n' + response
        return state, pending, response, params, neg_params, suggestions, excluded

    if intent is None or intent == 'ask_explanation':
        response = respondExplain(state)
    elif intent == 'ask_name':
        response = "My name is FinanceHelper. I hope that I can help you gain some useful information about stock."
    elif intent == 'thank':
        response = random.choice(
            ["It's my pleasure.", "I'm very happy to help you.", "You are welcome.", "I'm flattered."])
    elif intent == 'greet':
        response = respondGreet(message)
    elif intent == 'goodbye':
        response = random.choice(["bye bye, ", "goodbye, ", "see you, "]) + random.choice(
            ["wish you a good day", "i'm glad to help you next time"])
        return INIT, None, response, {}, {}, [], []

    if response is not None:
        return state, pending, response, params, neg_params, suggestions, excluded

    if state == AFFIRMED:
        response = respondExplain(AFFIRMED)
        return state, pending, response, params, neg_params, suggestions, excluded

    if intent == 'ask_stock_advice' or intent == 'choose_stock':
        params, neg_params, suggestions, excluded = {}, {}, [], []
    if not policy_rules.__contains__((state, intent)):
        if intent is None or state == INIT:
            response = "Sorry, please follow the guide or ask for guide in the form like 'How to ask questions?', thank you."
        else:
            # print(intent)
            response, params, neg_params, suggestions, excluded = respond(message, params, neg_params, suggestions,
                                                                          excluded)
    else:
        state, response, pending_state = policy_rules[(state, intent)]
        if response is None:
            response, params, neg_params, suggestions, excluded = respond(message, params, neg_params, suggestions,
                                                                          excluded)
        if pending is not None and state == EMAIL:
            state, response1, pending_state = policy_rules[pending]
            if response1 == None:
                response1, params, neg_params, suggestions, excluded = respond(message, params, neg_params, suggestions,
                                                                               excluded)
            response = response + '\n' + response1
        if pending_state is not None:
            pending = (pending_state, intent)
            response0, params, neg_params, suggestions, excluded = respond(message, params, neg_params, suggestions,
                                                                           excluded)
    return state, pending, response, params, neg_params, suggestions, excluded


def start(update, context):
    global params,neg_params,suggestions,excluded,state,pending
    update.message.reply_text(
        "Hi! I'm FinanceHelper. I hope that I can help you gain some useful information about stock.")
    #    reply_markup=markup
    params, neg_params, suggestions, excluded = {}, {}, [], []
    state = INIT
    pending = None


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def clean(update, context):
    rules = {
        'if (.*)': ["Do you really think it's likely that {0}", 'Do you wish that {0}', 'What do you think about {0}',
                    'Really--if {0}'],
        'do you think (.*)': ['if {0}? Absolutely.', 'No chance'],
        'do you remember (.*)': ['Did you think I would forget {0}', "Why haven't you been able to forget {0}",
                                 'What about {0}', 'Yes .. and?']}
    for pattern, r in rules.items():
        match = re.search(pattern, update.message.text)
        if match is not None:
            response = random.choice(r)
            var = match.group(1) if '{0}' in response else None
            if '{0}' in response:
                # Replace the pronouns of phrase
                phrase = replace_pronouns(phrase)
                # Calculate the response
                response = response.format(phrase)
            update.message.reply_text(response)


def chat(update, context):
    # update.message.reply_text(update.message.text)
    global state, pending, params, neg_params, suggestions, excluded
    state, pending, response, params, neg_params, suggestions, excluded= respond_state(state, pending, update.message.text, params, neg_params, suggestions, excluded)
    if state == INIT:
        update.message.reply_text(response,reply_markup=skip_markup)
    elif state == EMAIL:
        update.message.reply_text(response, reply_markup=restart_markup)
    elif state == ADVICE:
        update.message.reply_text(response, reply_markup=restart_markup)
    else:
        update.message.reply_text(response, reply_markup=markup)


def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater("764934002:AAEf-wUISlR0yaEiItAwUJiwp5nLoZAkRvo", use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # start
    dp.add_handler(CommandHandler("start", start))

    # clean
    dp.add_handler(MessageHandler(Filters.regex('if (.*)|do you think (.*)|do you remember (.*)'),clean))

    # chat
    dp.add_handler(MessageHandler(Filters.text,chat))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()