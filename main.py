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
import pandas as pd

from environs import Env

questions_path = "C:/Users/Honor/Documents/GitHub/Oge-tester/Questions.xlsx"
vars_path = "C:/Users/Honor/Documents/GitHub/Oge-tester/Vars.xlsx"
passings_path = "C:/Users/Honor/Documents/GitHub/Oge-tester/Passings.xlsx"

# # открываем файлы в качестве БД:
# df_questions = pd.read_excel(questions_path, index_col=None).reset_index(drop=True)
# df_vars = pd.read_excel(vars_path, index_col=None).reset_index(drop=True)
# df_passings = pd.read_excel(passings_path, index_col=None).reset_index(drop=True)


env = Env()
env.read_env()


def start_conversation(update, context):
    query = update.callback_query
    user_id = update.effective_user.id
    # print(update)
    username = update.effective_user.username

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

    df_vars = pd.read_excel(vars_path, index_col=None).reset_index(drop=True)

    # записать новый вариант в файл Vars.xlxs
    new_var_code = uniq_id
    new_quest = quest
    new_var_entry = [new_var_code, new_quest]
    df_extended = pd.DataFrame(new_var_entry).T  # преобразовываем список во временныый датафрейм из одной строки (такая технология сейчас в pandas)
    df_extended.columns = ['var', 'quest']
    df_vars = pd.concat([df_vars, df_extended])  # добавляем временный датафрейм к основному датафрейму
    with pd.ExcelWriter(vars_path, mode='a', if_sheet_exists='replace') as writer:
        df_vars.to_excel(writer, index=False)

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

    # получение прохождений
    kod = uniq_id  # интересующий нас код
    df_passings = pd.read_excel(passings_path, index_col=None).reset_index(drop=True)  # открываем файл с результатами
    df_passings_filtered = df_passings[(df_passings['var'] == kod)]  # вытаскиваем строки с нашим кодом
    quest = df_passings_filtered.iloc[0][['quest']].squeeze()  # номер задания у всех один, вытаскиваем его из первой строки
    df_out = df_passings_filtered[['user', 'time', 'task', 'answs']].copy()  # формируем таблицу выводных данных из строк

    var = {}
    for d in df_out.values.tolist():
        if not var.get(d[0]):
            var[d[0]] = {"dtm": d[1], "qst": {}}
        var[d[0]]["qst"][d[2]] = d[3]

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
        text=f"""Вариант: задание {quest}""",
        parse_mode=ParseMode.HTML
    )
    for usr in var:
        passing = var[usr]
        pass_time = ""

        timex = passing["dtm"]
        if timex >= 3600:
            pass_time += f"{timex//3600} ч. "
        pass_time += f"{int(timex//60%60)} мин."
        if timex < 3600:
            pass_time += f" {int(timex % 60)} сек. "

        text = f"""Прохождение @{usr}\nВремя прохождения: {pass_time}\nОтветы:\n"""

        res = 0
        for task in passing["qst"]:
            text += f"{task}. "
            text += "Верно" if passing["qst"][task] else "Ошибка"
            text += "\n"
            res += 1 if passing["qst"][task] else 0

        count = len(passing["qst"])
        text += f"Результат прохождения: {res}/{count}, {int(res/count*100)}%"
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
        text=f"""Всего прохождений: {len(var)}""",
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

    df_vars = pd.read_excel(vars_path, index_col=None).reset_index(drop=True)

    var_code = uniq_id
    var_code_entry = df_vars[(df_vars['var'] == var_code)]
    quest = var_code_entry[['quest']].squeeze()
    if not quest:
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
            text=f"""Задание {quest}\nВ качестве ответов вписывайте числа, без пробелов, дробные числа записывайте через точку\nПример ответа: -8.35""",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        context.user_data["quest"] = quest
        context.user_data["uniq_id"] = uniq_id
    return "START_TEST"


def take_test(update, context):
    global df_passings
    query = update.callback_query
    user_id = update.effective_user.id
    username = update.effective_user.username
    if not username:
        username = str(user_id)
    amount = 10

    quest = str(context.user_data["quest"])

    df_questions = pd.read_excel(questions_path, index_col=None).reset_index(drop=True)
    df_passings = pd.read_excel(passings_path, index_col=None).reset_index(drop=True)

    if context.user_data.get("numb"):
        text = update.message.text
        with open("answers.json", encoding="UTF-8") as file:
            data = json.load(file)
        true_ans = df_questions.loc[((df_questions['quest'] == float(quest)) & (df_questions['task'] == float(context.user_data["tasks"][context.user_data["numb"]-1])))][['true_ans']].squeeze()
        ans = float(text) == true_ans
        if ans:
            update.effective_message.reply_text(
                text=f"""Верно!""",
                parse_mode=ParseMode.HTML
            )
            context.user_data["res"] += 1
        else:
            if int(true_ans) == true_ans:
                true_ans = int(true_ans)
            update.effective_message.reply_text(
                text=f"""Неверно. Правильный ответ: {true_ans}""",
                parse_mode=ParseMode.HTML
            )

        # записать правильность ответа ученика по i-ому вопросу в файл Passings.xlxs
        passing_time = 0
        var_code = context.user_data["uniq_id"]
        passing_completed = False
        user = username
        quest_number = quest
        task_number = context.user_data["tasks"][context.user_data["numb"]-1]
        quest_answ = ans

        new_passing_entry = [  # записываем эти значения в список
            passing_time,
            var_code,
            passing_completed,
            user,
            quest_number,
            task_number,
            quest_answ
        ]

        df_extended = pd.DataFrame(new_passing_entry).T  # преобразовываем список во временныый датафрейм из одной строки (такая технология сейчас в pandas)
        df_extended.columns = ['time', 'var', 'completed', 'user', 'quest', 'task', 'answs']
        df_passings = pd.concat([df_passings, df_extended])  # добавляем временный датафрейм к основному датафрейму
        with pd.ExcelWriter(passings_path, mode='a', if_sheet_exists='replace') as writer:  # записываем дополненный датафрейм в исходный файл
            df_passings.to_excel(writer, index=False)
    else:
        context.user_data["numb"] = 0
        context.user_data["res"] = 0
        with open("answers.json", encoding="UTF-8") as file:
            data = json.load(file)
        context.user_data["tasks"] = []
        mx = len(df_questions.loc[(df_questions['quest'] == context.user_data["quest"])].axes[0])
        while len(context.user_data["tasks"]) < amount:
            n = r.randint(1, mx)
            if n not in context.user_data["tasks"]: context.user_data["tasks"].append(n)
        context.user_data["tasks"].sort()
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
        keyboard = [[InlineKeyboardButton("В меню", callback_data='menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.effective_message.reply_text(
            text=f"""{context.user_data["res"]}/{amount}""",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

        del context.user_data["numb"]
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
