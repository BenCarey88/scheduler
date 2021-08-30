"""Task classes."""

# there will be a BaseTask class,
# then there should be Routine and NonRoutine (better name) subclasses
# then NonRoutine should either have Project, Work, Health, Finance etc. subclasses
# or maybe just needs option to set type as Project/Work/etc. since the functionality
# will be the same in each

class BaseScheduleItem(object):
    def __init__(self):
        pass


class Routine(BaseScheduleItem):
    def __init__(self):
        pass


class Task(BaseScheduleItem):
    def __init__(self):
        pass
