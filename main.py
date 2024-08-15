import random as r
import time
import json
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
    ParseMode,
    LabeledPrice,
    InputMediaPhoto,
)
from telegram.ext import (
    Updater,
    Filters,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    PreCheckoutQueryHandler,
    ConversationHandler
)

from environs import Env

env = Env()
env.read_env()


def start_conversation(update, context):
    query = update.callback_query
    user_id = update.effective_user.id
    # print(update)
    username = update.effective_user.username

    data = {}
    with open("users.json", encoding="UTF-8") as file:
        data = json.load(file)

    # if username in data["admins"]:
    keyboard = [
        [
            InlineKeyboardButton("Создать вариант", callback_data='create_var'),
            InlineKeyboardButton("Пройти тест", callback_data='to_test'),
        ],
        [InlineKeyboardButton("Просмотреть прохождения", callback_data='passings')]
    ]
    text = "Вы находитесь в панели администратора"
    # else:
    #     keyboard = [
    #         [
    #             InlineKeyboardButton("пройти тест", callback_data='to_test'),
    #         ]
    #     ]
    #     text = "панель пользователя"
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_message.reply_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    return 'GREETINGS'

def create_var(update, context):
    query = update.callback_query
    user_id = update.effective_user.id
    username = update.effective_user.username

    keyboard = [
        [InlineKeyboardButton(f"Задание {i}", callback_data=f'question{i}')] for i in range(6, 20)
    ]
    keyboard.append([InlineKeyboardButton("в меню", callback_data='menu')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    # filepath = os.path.join(STATIC_ROOT, 'greetings.jpg')
    update.effective_message.reply_text(
        text=f"""Выберите номер задания (номера совпадают с фактическими)""",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

    return 'CREATE_VAR'

def quest6(update, context): return generate(update, context, 6)
def quest7(update, context): return generate(update, context, 7)
def quest8(update, context): return generate(update, context, 8)

def generate(update, context, quest):
    query = update.callback_query
    user_id = update.effective_user.id
    uniq_id = ""
    letters = "abcdefghijklmnopqrstvwxyzABCDEFGHIJKMNOPQRSTVWXYZ"
    for i in range(30):
        if r.randint(1, 2) == 1:
            uniq_id += str(r.randint(1, 9))
        else:
            uniq_id += r.choice(letters)

    with open("users.json", "r+", encoding="UTF-8") as file:
        data = json.load(file)
        data["vars"][uniq_id] = {"quest": quest, "passings": {}}
        file.seek(0)
        file.write(json.dumps(data))
        # file.truncate(0)
    keyboard = [
        [
            InlineKeyboardButton("в меню", callback_data='menu'),
            # InlineKeyboardButton("Сгенерировать", callback_data='generate'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # filepath = os.path.join(STATIC_ROOT, 'greetings.jpg')
    update.effective_message.reply_text(
        text=f"""<code>{uniq_id}</code>""",
        parse_mode=ParseMode.HTML
    )
    update.effective_message.reply_text(
        text=f"""Вставьте данный код перед прохождением теста""",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    return 'GENERATE'

def passings(update, context):
    query = update.callback_query
    user_id = update.effective_user.id

    update.effective_message.reply_text(
        text=f"""Вставьте код для просмотра прохождений.""",
        parse_mode=ParseMode.HTML
    )

    return "PASSINGS"


def get_passings(update, context):
    query = update.callback_query
    user_id = update.effective_user.id
    uniq_id = update.message.text

    with open("users.json", encoding="UTF-8") as file:
        data = json.load(file)
    var = data["vars"].get(uniq_id)
    if not var:
        keyboard = [
            [
                InlineKeyboardButton("в меню", callback_data='menu'),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.effective_message.reply_text(
            text=f"""Код не действителен\nВведите действующий код""",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        return "GET_PASSINGS"

    update.effective_message.reply_text(
        text=f"""Вариант: задание {var["quest"]}""",
        parse_mode=ParseMode.HTML
    )

    for passing in filter(lambda x: var["passings"][x]["completed"], list(var["passings"].keys())):
        pass_time = ""
        timex = var["passings"][passing]["time"]
        if timex >= 3600:
            pass_time += f"{timex//3600} ч. "
        pass_time += f"{int(timex//60%60)} мин."
        if timex < 3600:
            pass_time += f" {int(timex % 60)} сек. "
        text = f"""Прохождение @{passing}\nВремя прохождения: {pass_time}\nОтветы:\n"""
        for task in var["passings"][passing]["answs"]:
            text += f"{task}. "
            text += "Верно" if var["passings"][passing]["answs"][task] else "Ошибка"
            text += "\n"
        a = var["passings"][passing]["res"]
        count = len(var['passings'][passing]['answs'])
        text += f"Результат прохождения: {a}/{count}, {int(a/count*100)}%"
        update.effective_message.reply_text(
            text=text,
            parse_mode=ParseMode.HTML
        )
    keyboard = [
        [
            InlineKeyboardButton("в меню", callback_data='menu'),
            InlineKeyboardButton("проверить другой код", callback_data='passings'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_message.reply_text(
        text=f"""Всего прохождений: {len(var['passings'])}""",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

    return "GET_PASSINGS"


def to_test(update, context):
    query = update.callback_query
    user_id = update.effective_user.id

    update.effective_message.reply_text(
        text=f"""Вставьте код для прохождения теста.\nДля получения кода обратитесь к администратору""",
        parse_mode=ParseMode.HTML
    )

    return "TO_TEST"

def start_test(update, context):
    query = update.callback_query
    user_id = update.effective_user.id
    uniq_id = update.message.text
    with open("users.json", encoding="UTF-8") as file:
        data = json.load(file)
    var = data["vars"].get(uniq_id)
    if not var:
        keyboard = [
            [
                InlineKeyboardButton("в меню", callback_data='menu'),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.effective_message.reply_text(
            text=f"""Код не действителен\nОбратитесь к администратору для получения кода""",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    else:
        keyboard = [
            [
                InlineKeyboardButton("Начать тест", callback_data='take_test'),
                InlineKeyboardButton("Вернуться в меню", callback_data='menu'),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.effective_message.reply_text(
            text=f"""Задание {var["quest"]}\nВ качестве ответов вписывайте числа, без пробелов, дробные числа записывайте через точку\nПример ответа: -8.35""",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        context.user_data["var"] = var
        context.user_data["uniq_id"] = uniq_id
    return "START_TEST"


def take_test(update, context):
    query = update.callback_query
    user_id = update.effective_user.id
    username = update.effective_user.username
    if not username:
        username = str(user_id)
    amount = 10

    quest = str(context.user_data["var"]["quest"])

    # numb = context.user_data.get("numb")

    if context.user_data.get("numb"):
        text = update.message.text
        with open("answers.json", encoding="UTF-8") as file:
            data = json.load(file)
        ans = data["quests"][quest][context.user_data["tasks"][context.user_data["numb"]-1]-1] == text
        if ans:
            update.effective_message.reply_text(
                text=f"""Верно!""",
                parse_mode=ParseMode.HTML
            )
        else:
            update.effective_message.reply_text(
                text=f"""Неверно. Правильный ответ: {data["quests"][quest][context.user_data["tasks"][context.user_data["numb"]-1]-1]}""",
                parse_mode=ParseMode.HTML
            )
        # print(data["quests"][quest][context.user_data["tasks"][context.user_data["numb"]-1]-1], text)
        with open("users.json", "r+", encoding="UTF-8") as file:
            data = json.load(file)
            data["vars"][context.user_data["uniq_id"]]["passings"][username]["answs"][context.user_data["tasks"][context.user_data["numb"]-1]] = ans
            file.seek(0)
            file.write(json.dumps(data))
    else:
        context.user_data["numb"] = 0
        with open("answers.json", encoding="UTF-8") as file:
            data = json.load(file)
        context.user_data["tasks"] = []
        while len(context.user_data["tasks"]) < amount:
            n = r.randint(1, len(data["quests"][quest]))
            if n not in context.user_data["tasks"]: context.user_data["tasks"].append(n)
        context.user_data["tasks"].sort()
        with open("users.json", "r+", encoding="UTF-8") as file:
            data = json.load(file)
            data["vars"][context.user_data["uniq_id"]]["passings"][username] = {"completed": False, "answs": {}}
            file.seek(0)
            file.write(json.dumps(data))
        context.user_data["start_time"] = time.time()

    if context.user_data["numb"] < amount:
        context.user_data["numb"] += 1
        numb = str(context.user_data["tasks"][context.user_data["numb"]-1])
        # quest_str = str(quest)
        if len(quest) < 2: quest = "0" + quest
        if len(numb) < 2: numb = "0" + numb

        filename = f"quests/q{quest}.{numb}.png"

        with open(filename, 'rb') as file:
            update.effective_message.reply_photo(
                photo=file,
                parse_mode=ParseMode.HTML
            )
    else:
        with open("users.json", "r", encoding="UTF-8") as file:
            data = json.load(file)
            data["vars"][context.user_data["uniq_id"]]["passings"][username]["completed"] = True
            a = list(data["vars"][context.user_data["uniq_id"]]["passings"][username]["answs"].values()).count(True)
            data["vars"][context.user_data["uniq_id"]]["passings"][username]["res"] = a
            data["vars"][context.user_data["uniq_id"]]["passings"][username]["time"] = time.time() - context.user_data["start_time"]
        with open("users.json", "w", encoding="UTF-8") as file:
            file.seek(0)
            file.write(json.dumps(data))
        # a = list(data["vars"][context.user_data["uniq_id"]]["passings"][username]["answs"].values()).count(True)
        keyboard = [[InlineKeyboardButton("В меню", callback_data='menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.effective_message.reply_text(
            text=f"""{a}/{amount}""",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

        del context.user_data["numb"]
        del context.user_data["var"]
        del context.user_data["uniq_id"]

    return "TAKE_TEST"


def main():
    tg_token = env.str('TG_TOKEN')
    updater = Updater(token=tg_token, use_context=True)
    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_conversation)],
        states={
            'GREETINGS': [
                CallbackQueryHandler(create_var, pattern='create_var'),
                CallbackQueryHandler(to_test, pattern='to_test'),
                CallbackQueryHandler(passings, pattern='passings'),
            ],
            'CREATE_VAR': [
                CallbackQueryHandler(quest6, pattern='question6'),
                CallbackQueryHandler(quest7, pattern='question7'),
                CallbackQueryHandler(quest8, pattern='question8'),
                CallbackQueryHandler(start_conversation, pattern='menu'),
            ],
            'GENERATE': [
                CallbackQueryHandler(start_conversation, pattern='menu'),
                # CallbackQueryHandler(generate, pattern='СКУФ'),
            ],
            'PASSINGS': [
                MessageHandler(Filters.text, get_passings),
            ],
            'GET_PASSINGS': [
                CallbackQueryHandler(start_conversation, pattern='menu'),
                CallbackQueryHandler(passings, pattern='passings'),
            ],
            'TO_TEST': [
                MessageHandler(Filters.text, start_test),
            ],
            'START_TEST': [
                CallbackQueryHandler(start_conversation, pattern='menu'),
                CallbackQueryHandler(take_test, pattern='take_test'),
            ],
            'TAKE_TEST': [
                CallbackQueryHandler(start_conversation, pattern='menu'),
                MessageHandler(Filters.text, take_test),
            ]
        },
        fallbacks=[],
        per_chat=False
    )
    dispatcher.add_handler(conv_handler)
    start_handler = CommandHandler('start', start_conversation)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(CallbackQueryHandler(start_conversation, pattern='menu'))
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
