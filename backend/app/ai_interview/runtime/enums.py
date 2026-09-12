from enum import Enum

class RuntimeAction(str, Enum):
    INITIALIZE = "INITIALIZE"
    START = "START"
    PAUSE = "PAUSE"
    RESUME = "RESUME"
    ADVANCE_TOPIC = "ADVANCE_TOPIC"
    COMPLETE = "COMPLETE"
    FAIL = "FAIL"
    NO_ACTION = "NO_ACTION"
