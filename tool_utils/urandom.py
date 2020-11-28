RANDOM_MAX_RANGE = 2147483648 # 2^31
class Random():
    def __init__(self, seed=1):
        self.__seed = seed
    
    def __next(self):
        self.__seed = (self.__seed * 1103515245 + 12345) % RANDOM_MAX_RANGE
        return self.__seed

    def next_int(self, max=RANDOM_MAX_RANGE):
        return self.__next() * max // RANDOM_MAX_RANGE

    def next_float(self, max=1.0):
        return self.__next() * max / RANDOM_MAX_RANGE
