import json

FILE_NAME = 'tasks.json'


# Function to load the tasks from json file
def load_tasks():
    try:
        with open(FILE_NAME, 'r') as file:
            tasks = json.load(file)
    except FileNotFoundError:
        tasks = {}
    return tasks

# Function to save the tasks on json file
def save_tasks(tasks):
    with open(FILE_NAME, 'w') as file:
        json.dump(tasks, file, indent=4)

# Function to add a new task
def new_task(start_time, end_time, description, fixed=False):
    tasks = load_tasks()
    if fixed:
        task_type = 'fixed_tasks'
    else:
        task_type = 'extra_tasks'
    tasks[task_type][start_time] = [end_time, description]
    save_tasks(tasks)

# Function to list all the tasks
def list_tasks(fixed=True):
    tasks = load_tasks()
    task_type = 'fixed_tasks' if fixed else 'extra_tasks'
    task_list = tasks.get(task_type, {})

    return task_list

# Function to reset the tasks
def reset_tasks():
    save_tasks({})