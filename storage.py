from datetime import datetime
from threading import Lock

class TaskStorage:
    def __init__(self):
        self.tasks = {}
        self.next_id = 1
        self.lock = Lock()

    def add_task(self, text):
        with self.lock:
            task_id = self.next_id
            self.tasks[task_id] = {
                'text': text,
                'completed': False,
                'created_at': datetime.now(),
                'completed_at': None
            }
            self.next_id += 1
            return task_id

    def get_all_tasks(self):
        with self.lock:
            return self.tasks.copy()

    def mark_task_complete(self, task_id):
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id]['completed'] = True
                self.tasks[task_id]['completed_at'] = datetime.now()
                return True
            return False
