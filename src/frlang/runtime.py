"""运行时和调度器。"""

from collections import deque
from typing import Callable

from .future import Future, FutureState


Task = Callable[[], None]


class Runtime:
    """管理任务队列和 Future 调度。"""

    def __init__(self) -> None:
        self.tasks: deque[Task] = deque()

    def schedule(self, task: Task) -> None:
        """把任务加入队列。"""
        self.tasks.append(task)

    def run(self) -> None:
        """运行调度循环。"""
        while self.tasks:
            self.run_next()

    def run_until_future(self, future: Future) -> None:
        """运行任务队列，直到指定 Future 完成或队列耗尽。"""
        while future.state is FutureState.PENDING and self.tasks:
            self.run_next()

    def run_next(self) -> None:
        """运行队列中的下一个任务。"""
        task = self.tasks.popleft()
        task()
