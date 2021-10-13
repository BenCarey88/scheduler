"""Ui utility functions."""


from contextlib import contextmanager


@contextmanager
def suppress_signals(*QObjects_list):
    """contextmanager to temporarily blocks all signals of passed QObjects.

    Args:
        QObjects_list (list(QtCore.QObject)) list of QObjects whose
            signals we want to block.
    """
    previous_state = {}
    for obj in QObjects_list:
        previous_state[obj] = obj.blockSignals(True)
    yield
    for obj in QObjects_list:
        obj.blockSignals(previous_state[obj])
