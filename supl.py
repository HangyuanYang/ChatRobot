# Import necessary modules
import re
import random


def replace_pronouns(message):
    message = message.lower()
    if 'me' in message:
        return re.sub('me', 'you', message)
    if 'i' in message:
        return re.sub('i', 'you', message)
    elif 'my' in message:
        return re.sub('my', 'your', message)
    elif 'your' in message:
        return re.sub('your', 'my', message)
    elif 'you' in message:
        return re.sub('you', 'me', message)

    return message


# Define find_name()
def find_name(message):
    name = None
    # Create a pattern for finding capitalized words
    name_pattern = re.compile('[A-Z]{1}[a-z]*')
    # Get the matching words in the string
    name_words = name_pattern.findall(message)
    if len(name_words) > 0:
        # Return the name if the keywords are present
        name = ' '.join(name_words)
    return name


# Define respond()
def respondGreet(message):
    # Find the name
    name = find_name(message)
    if name is None:
        return random.choice(["Hi! Enjoy the our chat time.","Hello! Enjoy today"])
    else:
        return "Hello, {0}! I'm glad to help you query about stock Info".format(name)


def respondExplain(state):
    INIT, EMAIL, ADVICE, AFFIRMED = range(4)
    if state == INIT:
        return "well, you can type in your email address to subscribe the newest stock news or click on 'skip_email' button" \
               "\nBesides:\n1.You can query about one stock in this form: \n" \
                        "  I'd like to know sth about AAPL;\n  tell me sth about TSLA;\n  do you know TXG stock\n" \
               "2.You can ask for some recommendation in this form:\n" \
                        "  tell me sth about stock symbols;recommend sth\n  what stock can you introduce to me;\n" \
                        "  which stock do you know;give me some stock advice;\nrecommend some stock\n" \
               " Besides, you can further confine the country/state/city/exchange of the corresponding company like this:\n" \
               " not in the US,at the Foshan,in Hollywood,in NASDAQ,etc."

    elif state == ADVICE:
        return "affirm the chosen stock or refuse the recommendation please"
    elif state == AFFIRMED:
        return "just select the information you interested in or click on 'restart' to choose another stock"
    else:
        return "1.You can query about one stock in this form: \n" \
                        "  I'd like to know sth about AAPL;\n  tell me sth about TSLA;\n  do you know TXG stock\n" \
               "2.You can ask for some recommendation in this form:\n" \
                        "  tell me sth about stock symbols;recommend sth\n  what stock can you introduce to me;\n" \
                        "  which stock do you know;give me some stock advice;\n" \
               " Besides, you can further confine the country/state/city/exchange of the corresponding company like this:\n" \
               " not in the US,at the Foshan,in Hollywood,in NASDAQ,etc."