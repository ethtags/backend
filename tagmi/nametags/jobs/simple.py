"""
Simple job module, remove after wiring views in.
"""
import time


def long_running_func():
    """ Simple job function. """
    print("hello i am a worker running a job")
    time.sleep(10)
    return True
