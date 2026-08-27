"""Future 对象。"""

from enum import Enum, auto
from typing import Any, Callable


class FutureState(Enum):
    """Future 当前状态。"""

    PENDING = auto()
    RESOLVED = auto()
    REJECTED = auto()


class Future:
    """FRLanguage 的最小 Future 模型。"""

    def __init__(self) -> None:
        self.state = FutureState.PENDING
        self.value: Any = None
        self.error: Exception | None = None
        self.callbacks: list[Callable[["Future"], None]] = []

    def resolve(self, value: Any) -> None:
        """把 Future 标记为成功完成。"""
        self.complete(FutureState.RESOLVED, value=value)

    def reject(self, error: Exception) -> None:
        """把 Future 标记为失败。"""
        self.complete(FutureState.REJECTED, error=error)

    def complete(
        self,
        state: FutureState,
        *,
        value: Any = None,
        error: Exception | None = None,
    ) -> None:
        if self.state is not FutureState.PENDING:
            raise RuntimeError("Future 已经完成")

        self.state = state
        self.value = value
        self.error = error

        for callback in self.callbacks:
            callback(self)

    def add_callback(self, callback: Callable[["Future"], None]) -> None:
        """注册完成回调；如果已经完成则立即调用。"""
        if self.state is FutureState.PENDING:
            self.callbacks.append(callback)
            return

        callback(self)
