import telebot
import schedule
import os
import time
import threading
from datetime import datetime, timedelta
from telegramdata import load_tasks, save_tasks, new_task, list_tasks, reset_tasks



key_api = os.environ.get('KEY_API')
chat_id = os.environ.get('CHAT_ID')
port = os.environ.get('PORT')
tz = os.environ.get('TZ')
bot = telebot.TeleBot(key_api)
bot.delete_webhook()


### Assistant Functions ###
# Function to send a task reminder
def send_reminder(task_info):
    start_time, end_time, description = task_info
    bot.send_message(chat_id, f"Lembrete:\n\n{start_time} - {end_time}: {description}")


# Verification if is time to send a reminder
def schedule_task_reminders():
    tasks = load_tasks()
    for task_type, task_dict in tasks.items():
        for start_time, task_info in task_dict.items():
            if start_time not in schedule_tasks:
                end_time, description = task_info
                schedule.every().day.at(start_time).do(send_reminder, task_info=(start_time, end_time, description))
                schedule_tasks.add(start_time)


# Function to reschedule tasks that have passed for the next working day
def reschedule_tasks():
    today = datetime.now()
    next_workday = today + timedelta(days=1)
    while next_workday.weekday() >= 5:
        next_workday += timedelta(days=1)

    tasks = load_tasks()
    for task_type, task_dict in tasks.items():
        for start_time, task_info in task_dict.items():
            task_datetime = datetime.combine(today.date(), datetime.strptime(start_time, "%H:%M").time())
            if task_datetime < today:
                new_start_time = datetime.combine(next_workday.date(), datetime.strptime(start_time, "%H:%M").time())
                new_start_time_str = new_start_time.strftime("%H:%M")
                task_dict[new_start_time_str] = task_info
                del task_dict[start_time]
    
    save_tasks(tasks)


# Function to execute the bot.polling() in a separate thread
def polling_thread():
    try:
        while True:
            bot.polling(none_stop=True)
    except Exception as e:
        print(f"Erro no polling_thread: {e}")


# Function to remember the tasks in the morning
def morning_message():
    fixed_tasks = list_tasks(fixed=True)
    extra_tasks = list_tasks()

    today = datetime.now().weekday()

    if today < 5:
        good_morning = 'Bom dia Senhor! Aqui estão as suas obrigações para hoje:\n\n'
        if fixed_tasks:
            good_morning += 'Tarefas Fixas:\n'
            for time, task_info in sorted(fixed_tasks.items(), key=lambda x: x[0]):
                end_time, description = task_info
                good_morning += f"{time} - {end_time}: {description}\n"
        else:
            good_morning += 'Não há tarefas fixas para hoje, Senhor. Tenha um ótimo dia!\n\n'
    
        if extra_tasks:
            good_morning += '\nTarefas extras:\n'
            for time, task_info in sorted(extra_tasks.items(), key=lambda x: x[0]):
                end_time, description = task_info
                good_morning += f"{time} - {end_time}: {description}\n"
        else:
            good_morning += "Não há tarefas extras para hoje, Senhor."

        bot.send_message(chat_id, good_morning)
    else:
        bot.send_message(chat_id, "Bom dia, Senhor! Aproveite o fim de semana.")


# Load fixed tasks in the beginning
def load_fixed_tasks():
    tasks = load_tasks()
    fixed_tasks = tasks.get('fixed_tasks', {})
    today = datetime.now().weekday()
    if today < 5:
        for start_time, task_info in fixed_tasks.items():
            if isinstance(task_info, list):
                end_time, description = task_info
                new_task(start_time, end_time, description, fixed=True)
            else:
                new_task(start_time, task_info, fixed=True)


# Function to process the type of task to add
def process_task_type(message):
    task_type = message.text.lower()
    if task_type == '1':
        bot.reply_to(message, 'Início (HH:MM):')
        bot.register_next_step_handler(message, lambda msg: process_start_time(msg, fixed=True))
    elif task_type == '2':
        bot.reply_to(message, 'Início (HH:MM):')
        bot.register_next_step_handler(message, lambda msg: process_start_time(msg, fixed=False))
    else:
        bot.reply_to(message, "Tipo de tarefa inválido, escolha 'fixa' ou 'extra'.")


# Process start time for the task
def process_start_time(message, fixed):
    start_time = message.text.strip()
    bot.reply_to(message, 'Fim (HH:MM):')
    bot.register_next_step_handler(message, lambda msg: process_description(msg, start_time, fixed))


# Process description for the task
def process_description(message, start_time, fixed):
    end_time = message.text.strip()
    bot.reply_to(message, 'Qual a descrição da tarefa?')
    bot.register_next_step_handler(message, lambda msg: add_task(msg, start_time, end_time, fixed))


# Function to add the task based on user input
def add_task(message, start_time, end_time, fixed):
    description = message.text.strip()
    tasks = load_tasks()

    if start_time in tasks.get('fixed_tasks', {}) or start_time in tasks.get('extra_tasks', {}):
        bot.reply_to(message, f"Senhor, já existe uma tarefa agendada para às {start_time}. Por favor, escolha outro horário.")
        return

    new_task(start_time, end_time, description, fixed=fixed)
    bot.reply_to(message, "Tarefa adicionada com sucesso, Senhor!")
    schedule_task_reminders()


# Function to process the edition of the task
def process_edit_task_type(message):
    task_type = message.text.lower()
    if task_type == '1':
        bot.reply_to(message, 'Por favor, digite o horário início da tarefa que deseja editar (HH:MM):')
        bot.register_next_step_handler(message, process_edit_fixed_task)
    elif task_type == '2':
        bot.reply_to(message, 'Por favor, digite o horário início da tarefa que deseja editar (HH:MM):')
        bot.register_next_step_handler(message, process_edit_extra_task)
    else:
        bot.reply_to(message, "Tipo de tarefa inválido, escolha 'fixa' ou 'extra'.")


# Function to do the edit of the task
def perform_edit_task(message, old_time, new_start_time, new_end_time, fixed):
    new_description = message.text.strip()
    tasks = load_tasks()
    task_type = 'fixed_tasks' if fixed else 'extra_tasks'
    task_dict = tasks.get(task_type, {})

    if old_time in task_dict:
        task_info = task_dict.pop(old_time)
        task_dict[new_start_time] = [new_end_time, new_description] if fixed else [new_end_time, new_description]
        save_tasks(tasks)
        bot.reply_to(message, f"Tarefa editada com sucesso, Senhor!")
        schedule_task_reminders()
    else:
        bot.reply_to(message, f"Tarefa não encontrada no horário {old_time}.")


# Function to process editing a fixed task
def process_edit_fixed_task(message):
    old_time = message.text.strip()
    bot.reply_to(message, 'Início (HH:MM):')
    bot.register_next_step_handler(message, lambda msg: process_new_start_time(msg, old_time, fixed=True))


# Function to process editing an extra
def process_edit_extra_task(message):
    old_time = message.text.split()[0]
    bot.reply_to(message, 'Início (HH:MM):')
    bot.register_next_step_handler(message, lambda msg: process_new_start_time(msg, old_time, fixed=False))


# Function to process the new start time for the task
def process_new_start_time(message, old_time, fixed):
    new_start_time = message.text.strip()
    bot.reply_to(message, 'Fim (HH:MM):')
    bot.register_next_step_handler(message, lambda msg: process_new_end_time(msg, old_time, new_start_time, fixed))


# Function to process the new hour from the task
def process_new_end_time(message, old_time, new_start_time, fixed):
    new_end_time = message.text.strip()
    bot.reply_to(message, 'Por favor, digite a nova descrição da tarefa.')
    bot.register_next_step_handler(message, lambda msg: perform_edit_task(msg, old_time, new_start_time, new_end_time, fixed))


# Process the removal of a fixed tasks
def process_remove_fixed_task(message):
    time_to_remove = message.text.split()[0]
    remove_task(time_to_remove, fixed=True, message=message)


# Process the removal of an extra task
def process_remove_extra_task(message):
    time_to_remove = message.text.split()[0]
    remove_task(time_to_remove, fixed=False, message=message)


# Function to process the type of task to remove
def process_remove_task_type(message):
    task_type = message.text.split()[0].lower()
    if task_type == '1':
        bot.reply_to(message, 'Por favor, digite o horário de início da tarefa que deseja remover. (HH:MM)')
        bot.register_next_step_handler(message, process_remove_fixed_task)
    elif task_type == '2':
        bot.reply_to(message, 'Por favor, digite o horário de início da tarefa que deseja remover. (HH:MM)')
        bot.register_next_step_handler(message, process_remove_extra_task)
    else:
        bot.reply_to(message, "Tipo de tarefa inválido, escolha 'fixa' ou 'extra'.")


# Function to do the process for remove a task
def remove_task(time_to_remove, fixed, message):
    time_to_remove = message.text.split()[0]
    tasks = load_tasks()

    if fixed:
        task_dict = tasks.get('fixed_tasks', {})
    else:
        task_dict = tasks.get('extra_tasks', {})

    if time_to_remove in task_dict:
        del task_dict[time_to_remove]
        save_tasks(tasks)
        bot.reply_to(message, 'Tarefa removida com sucesso, Senhor! ')
    else:
        bot.reply_to(message, f"Tarefa não encontrada para o horário {time_to_remove}")



### Comands to Telegram bot ###
# Comand to salud
@bot.message_handler(func=lambda message: message.text.lower() == "task")
def handle_messages(message):
    bot.reply_to(message, '''Olá Sr.Gustavo! O que deseja?\n         
. listar - Exibir as obrigações do dia.
. adicionar - Adicionar uma nova tarefa.
. editar - Editar uma tarefa.
. remover - Remover uma tarefa.
. lembrar - Exibir a obrigação mais próxima.''')


# Comand to list the fixed and extra tasks     
@bot.message_handler(func=lambda message: message.text.lower() == "listar")
def list_tasks_handler(message):
    fixed_tasks = list_tasks(fixed=True)
    extra_tasks = list_tasks(fixed=False)

    task_list = 'Tarefas Fixas:\n\n'
    if task_list:
        if fixed_tasks:
            for start_time, task_info in sorted(fixed_tasks.items(), key=lambda x: x[0]):
                if isinstance(task_info, list) and len(task_info) >= 2:
                    end_time, description = task_info[:2]
                    task_list += f"{start_time} - {end_time}: {description}\n"
                elif isinstance(task_info, dict):
                    end_time = task_info.get('end_time', '')
                    description = task_info.get('description', '')
                    task_list += f"{start_time} - {end_time}: {description}\n"
        else:
            task_list = 'Sem obrigações hoje, Senhor. Aproveite o final de semana!'
                
        if extra_tasks:
            task_list += '\nTarefas Extras:\n\n' 
            for start_time, task_info in sorted(extra_tasks.items(), key=lambda x: x[0]):
                if isinstance(task_info, list) and len(task_info) >= 2:
                    end_time, description = task_info[:2]
                    task_list += f"{start_time} - {end_time}: {description}\n"
                elif isinstance(task_info, dict):
                    end_time = task_info.get('end_time', '')
                    description = task_info.get('description', '')
                    task_list += f"{start_time} - {end_time}: {description}\n"
        else:
            task_list += '\nNão há tarefas extras, Senhor.'
    else:
        bot.reply_to(message, "Sem tarefas, Senhor. Aproveite para tirar um tempo livre!") 

    bot.reply_to(message, task_list)


# Comand to remember the next near task
@bot.message_handler(func=lambda message: message.text.lower() == "lembrar")
def remember_next_task(message):
    all_tasks = {**list_tasks(fixed=True), **list_tasks(fixed=False)}
    today = datetime.now()
    actual_hour = today.strftime("%H:%M")
    next_task = [(time, task) for time, task in all_tasks.items() if time >= actual_hour]
    
    # Send the next task
    if next_task:
        next_time, next_task = min(next_task, key=lambda x: x[0])
        bot.reply_to(message, f"Aqui está a sua próxima tarefa:\n\n{next_time} - {next_task[0]}: {next_task[1]}")
    else:
        bot.reply_to(message, "Não há mais tarefas agendadas para hoje, Senhor.")


# Comand to add a new task
@bot.message_handler(func=lambda message: message.text.lower() == "adicionar")
def add_new_tasks(message):
    bot.reply_to(message, 'Por favor, escolha o tipo de tarefa que deseja adicionar:\n[1] Fixa\n[2] Extra')
    bot.register_next_step_handler(message, process_task_type)
    schedule_task_reminders()


# Comand to edit a task
@bot.message_handler(func=lambda message: message.text.lower() == "editar")
def edit_task_handler(message):
    bot.reply_to(message, 'Por favor, escolha o tipo de tarefa que deseja editar:\n[1] Fixa\n[2] Extra')
    bot.register_next_step_handler(message, process_edit_task_type)


# Comand to remove a task
@bot.message_handler(func=lambda message: message.text.lower() == "remover")
def remove_task_handler(message):
    bot.reply_to(message, 'Por favor, escolha o tipo de tarefa deseja remover.\n[1] Fixa\n[2] Extra')
    bot.register_next_step_handler(message, process_remove_task_type)


@bot.message_handler(func=lambda message: message.text.lower() == "horas")
def time_now(message):
    today = datetime.now()
    bot.reply_to(message, f"Agora são {today}, Senhor")



# To storage tasks
schedule_tasks = set()


# Reminder programation
schedule_task_reminders()
schedule.every().day.at("05:30").do(morning_message)
schedule.every().saturday.at("00:00").do(reset_tasks)
schedule.every().hour.do(reschedule_tasks)


# Start the thread for the bot.polling
threading.Thread(target=polling_thread).start()


# Call load fixed tasks
load_fixed_tasks()


# Main bot loop
while True:
    schedule.run_pending()
    time.sleep(1)