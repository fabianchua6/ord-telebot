import telebot as tb
import sqlite3
import datetime as dt
from numpy import busday_count
from random import choice as randomizer
from time import sleep
from dateutil.relativedelta import relativedelta as rd

token = "xxxxx"  # replace with your token
bot = tb.AsyncTeleBot(token)
print('Bot Awake')  # Bot is awake

holidays = {
    'New Year\'s Day': '2020-01-01',
    'CNY Observed': '2020-01-27',
    'Good Friday': '2020-04-10',
    'Labour Day': '2020-05-01',
    'Vesak Day': '2020-05-07',
    'Hari Raya Puasa Observed': '2020-05-25',
    'Hari Raya Haji': '2020-07-31',
    'National Day Observed': '2020-08-10',
    'Deepavali': '2020-11-14',
    'Christmas Day': '2020-12-25',
}  # According to Singapore Official Holiday


class User:
    def __init__(self, name):
        self.chatid = None
        self.name = name
        self.BMTdate = None
        self.ORDdate = None


### SQL things ###

db = sqlite3.connect("NSF.db", check_same_thread=False)  # contains user's details

c = db.cursor()


def add_user(chatid):
    q = 'INSERT INTO NSF (chatid, creation) VALUES (?, ?)'
    v = (chatid, dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    c.execute(q, v)
    print('User added...')
    db.commit()


def select_user(chatid):
    q = 'SELECT * FROM NSF WHERE chatid = ?'
    v = (chatid,)
    c.execute(q, v)
    existing = c.fetchone()
    print('Selecting user...')
    if existing is None:
        add_user(chatid)

    else:
        print(f'User selected:\n'
              f'Chat ID: {existing[0]}\n'
              f'Name: {existing[1]}\n'
              f'Enlistment Date: {existing[2]}\n'
              f'ORD Date: {existing[3]}\n')
        return existing


def update_user(chatid, first_name, bmtdate, orddate):
    q = 'UPDATE NSF SET first_name = ?, BMTdate = ?, ORDdate = ?, updated = ? WHERE chatid = ?'
    v = (first_name, bmtdate, orddate, dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), chatid)
    c.execute(q, v)
    db.commit()
    print(f'\n'
          f'=====Updated User=====\n'
          f'Chat ID : {User.chatid}\n'
          f'Name: {User.name}\n'
          f'BMT Date: {User.BMTdate}\n'
          f'ORD Date: {User.ORDdate}\n'
          f'======================\n')


def delete_user(chatid):
    q = 'DELETE FROM NSF where chatid = ?'
    v = (chatid,)
    c.execute(q, v)
    print('User deleted...')
    db.commit()


### telebot things ###

def dateregex(input):
    try:
        if input == '/quit':
            print('Process stopped')
            return 0
        else:
            x = dt.datetime.strptime(input, "%d-%m-%Y").date()
    except ValueError:
        x = dt.datetime.strptime(input, "%Y-%m-%d").date()
    return x


def ord_calculator(m):
    x = select_user(m.chat.id)
    User.BMTdate = dateregex(x[2])
    User.ORDdate = dateregex(x[3])
    today = dt.date.today()
    days_remaining = (User.ORDdate - today).days
    print(days_remaining, "days remaining")
    days_in_service = (today - User.BMTdate).days
    print(days_in_service, "days in service")
    percentage_completed = round(days_in_service / (User.ORDdate - User.BMTdate).days * 100, 2)
    print(percentage_completed, "% completed")
    working_days = busday_count(today, User.ORDdate, holidays=list(holidays.values()))
    print(working_days, "working days")

    markup = tb.types.ReplyKeyboardRemove(selective=False)
    bot.reply_to(m,
                 'Alright gennermen, Encik cowculate for you liao!\n'
                 f'\n*Date of Enlistment 🗓: {User.BMTdate.strftime("%d %b %Y ")}*'
                 f'\n*Operationally Ready Date 🗓: {User.ORDdate.strftime("%d %b %Y ")}*'
                 f'\n\nYou have *{str(days_remaining)} days* left to ORD. '
                 f'\n*{str(working_days)} working days* more to go! '
                 f'\nYou are *{str(percentage_completed)}%* there!',
                 parse_mode='markdown', reply_markup=markup)


@bot.message_handler(commands=['feedback'])
def feedback(m):
    bot.reply_to(m, "Hit me up @ t.me/FakeEncikTan to talk about anything under the sun. 😉")


@bot.message_handler(func=lambda message: True, content_types='sticker')
def send_sticker(m):
    bot.reply_to(m, 'Encik dunno how to use sticker ones la walaoz')


@bot.message_handler(commands=['delete'])
def delete(m):
    User.chatid = m.chat.id
    x = select_user(User.chatid)
    if x is None:
        bot.reply_to(m, "No records to delete.")

    else:
        delete_user(User.chatid)
        print('Records deleted')
        bot.reply_to(m, "Your records are deleted.")


@bot.message_handler(commands=['edit'])
def edit(m):
    User.chatid = m.chat.id
    bot.send_chat_action(m.chat.id, 'typing')
    markup = tb.types.ForceReply(selective=True)
    bot.send_message(m.chat.id, f"Please enter your Enlistment date in *DD-MM-YYYY* format\n"
                                f"*/quit* to cancel.", parse_mode='markdown', reply_markup=markup)
    bot.register_next_step_handler(m, bmt_date)


@bot.message_handler(commands=['start'])
def welcome(m):
    User.name = m.from_user.first_name
    User.chatid = m.chat.id
    x = select_user(User.chatid)
    if x is None or x[2] is None:
        now = dt.datetime.now().time()
        print('Time:', now)
        if dt.time(5, 00) <= now <= dt.time(11, 59):
            greetings = 'Good Morning! 🌞 '
        elif dt.time(12, 00) <= now <= dt.time(18, 59):
            greetings = 'Good Afternoon!'
        else:
            bot.send_message(m.chat.id, '😴')
            bot.send_chat_action(m.chat.id, 'typing')
            sleep(1.5)
            bot.send_message(m.chat.id, 'Encik is asleep alr la what you want?')
            greetings = 'Light out oredi you still cme and bother me?! Nvm...'
            sleep(1)

        bot.reply_to(m,
                     f"{greetings}\nEncik Tan is here to help you count down to your Pink IC.\nPlease acknowledge ok.")
        bot.register_next_step_handler(m, bmt_message)

    else:
        bot.reply_to(m, f"Ahh!! Encik Tan found your record liao...")
        bot.send_chat_action(m.chat.id, 'typing')
        sleep(1.5)
        bot.send_message(m.chat.id, "Your Pink IC still nowhere to be found tho... 🤣")
        sleep(1.5)
        ord_calculator(m)


def bmt_message(m):
    try:
        bot.send_chat_action(m.chat.id, 'typing')
        markup = tb.types.ForceReply(selective=True)
        bot.send_message(m.chat.id, f"Please enter your Enlistment date in *DD-MM-YYYY* format\n"
                                    f"*/quit* to cancel.", parse_mode='markdown', reply_markup=markup)
        bot.register_next_step_handler(m, bmt_date)

    except Exception:
        bot.reply_to(m, 'Oooops! Please forward this to t.me/FakeEncikTan to report this bug #bmt_m')
        return


def bmt_date(m):
    try:
        test = dateregex(m.text)
        if test == 0:
            bot.reply_to(m, f'Encik is sad to see you go..  *˚‧º·(˚ ˃̣̣̥᷄⌓˂̣̣̥᷅ )‧º·˚*', parse_mode='markdown')
            delete_user(User.chatid)
        else:
            User.BMTdate = test
            print(f'Enlistment Date: {User.BMTdate}')
            markup = tb.types.ReplyKeyboardMarkup(row_width=1)
            itembtn1 = tb.types.KeyboardButton('22 months')
            itembtn2 = tb.types.KeyboardButton('24 months')
            markup.add(itembtn1, itembtn2)
            bot.reply_to(m, f"Ok, please enter your service duration.\n"
                            f"*/quit* to cancel.", parse_mode='markdown', reply_markup=markup)
            bot.register_next_step_handler(m, whenord)

    except ValueError:
        bot.reply_to(m, 'Semula, please re-enter your Enlistment date in the correct format.')
        bot.register_next_step_handler(m, bmt_message)


def whenord(m):
    try:
        if m.text == '22 months':
            User.ORDdate = User.BMTdate + rd(months=22) - dt.timedelta(days=1)
            update_user(m.chat.id, m.from_user.first_name, User.BMTdate, User.ORDdate)
            ord_calculator(m)
        elif m.text == '24 months':
            User.ORDdate = User.BMTdate + rd(months=24) - dt.timedelta(days=1)
            update_user(m.chat.id, m.from_user.first_name, User.BMTdate, User.ORDdate)
            ord_calculator(m)
        elif m.text == '/quit':
            bot.reply_to(m, f'Encik is sad to see you go..  *˚‧º·(˚ ˃̣̣̥᷄⌓˂̣̣̥᷅ )‧º·˚*', parse_mode='markdown')
            delete_user(m.chat.id)
        else:
            bot.reply_to(m, f'Semula, please key in only *"22 months"* or *"24 months"* or use the buttons.',
                         parse_mode='markdown')
            bot.register_next_step_handler(m, whenord)

    except AttributeError:
        return

    except Exception as e:
        bot.reply_to(m, 'Oooops! Please forward this to t.me/FakeEncikTan to report this bug #whenord')
        print(e)
        print("whenord not working")
        return

# TODO: countdown to public holiday/next payday (use another command /holiday, countdown to next holiday)


@bot.message_handler(commands=['ippt'])
def ippt(m):
    bot.send_message(m.chat.id, 'Check out t.me/IPPTCalculatorBot to calculate your IPPT scores!')


@bot.message_handler(commands=['ordlo'])
def ordlo(m):
    x = select_user(m.chat.id)
    if x is None or x[2] is None:
        bot.reply_to(m, f'No date records found. \nPlease use /start to start entering your dates.')
    else:
        ord_calculator(m)


@bot.message_handler(func=lambda m: True)
def hi(m):
    try:
        bot.send_chat_action(m.chat.id, 'typing')
        list_of_words = ['Wait ah, Encik at siamdiu sia...',
                       '/ordlo to see when u ord',
                       'You want to press /start or you want sign extra?',
                       'before i knock you down, press /start hor!',
                       'Hello, please use command /start to start. :D',
                       'Sometimes if I don\'t reply, I am at siamdiu... shhh...'
                       ]

        bot.send_message(m.chat.id, randomizer(list_of_words))

    except Exception:
        bot.reply_to(m, 'Oooops! Please forward this to t.me/FakeEncikTan to report this bug #hi')


class MyException(Exception):
    pass


bot.infinity_polling(none_stop=True, timeout=15)
