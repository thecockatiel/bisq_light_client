from collections.abc import Callable
from PyQt5.QtCore import QObject, QEvent


class ClickFilter(QObject):

    def __init__(self, callback: Callable[[], None], parent=None):
        super().__init__(parent)
        self._callback = callback

    def eventFilter(self, obj: "QObject", event: "QEvent"):
        if event.type() == QEvent.Type.MouseButtonRelease:
            self._callback()
        return super().eventFilter(obj, event)
