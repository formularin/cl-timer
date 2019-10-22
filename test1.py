import time
import timeit

# these are the amounts of time the processes will take for each frame.
times = [0.01, 0.01, 0.01, 0.01, 0.01]


def func():
    delay = 0
    for t in times:
        start_time = time.time()
        
        time.sleep(t)

        duration = time.time() - start_time
        if (duration + delay) > 0.01:
            delay -= 0.01 - duration
        else:
            time.sleep(0.01 - (duration + delay))

print((timeit.timeit(func, number=100)) / 100)