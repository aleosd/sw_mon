#! /usr/bin/python3

import time


class Timer():
    """Usage:
    with Timer(verbose=True) as t:
        timing_function()
    """
    def __init__(self, verbose=False):
        self.verbose = verbose

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = time.time()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000
        if self.verbose:
            print('Running time {} s'.format(self.secs))
