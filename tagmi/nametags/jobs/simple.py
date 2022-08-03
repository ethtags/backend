import time
from django_rq import job

@job
def long_running_func():
    print("hello i am a worker running a job")
    time.sleep(10)
    return True
