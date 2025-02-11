from datetime import datetime
from threading import Lock

class TaskStorage:
    def __init__(self):
        self.tasks = {}
        self.next_id = 1
        self.lock = Lock()
        self.categories = set()  # Store unique categories

    def add_task(self, text, category=None):
        with self.lock:
            task_id = self.next_id
            self.tasks[task_id] = {
                'text': text,
                'category': category,
                'completed': False,
                'created_at': datetime.now(),
                'completed_at': None
            }
            if category:
                self.categories.add(category)
            self.next_id += 1
            return task_id

    def get_all_tasks(self):
        with self.lock:
            return self.tasks.copy()

    def get_tasks_by_category(self, category):
        with self.lock:
            return {
                task_id: task for task_id, task in self.tasks.items()
                if task['category'] == category
            }

    def get_categories(self):
        with self.lock:
            return sorted(list(self.categories))

    def mark_task_complete(self, task_id):
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id]['completed'] = True
                self.tasks[task_id]['completed_at'] = datetime.now()
                return True
            return False

    def set_task_category(self, task_id, category):
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id]['category'] = category
                if category:
                    self.categories.add(category)
                return True
            return False