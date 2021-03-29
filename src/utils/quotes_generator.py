import random
import threading
import time
from threading import Thread
from src.entity.symbol import Symbol
from src.conf.config_parser import ConfigParser


class QuotesGenerator(Thread):
    def __init__(self):
        super().__init__(daemon=True)
        config_parser = ConfigParser()
        self.config = config_parser.parse_config('quotes_generator')
        self.current_quotes = dict()
        self._stop = threading.Event()

    # function using _stop function
    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(QuotesGenerator, cls).__new__(cls)
        return cls.instance

    def run(self):
        while True:
            if self.stopped():
                return
            self.current_quotes = {
                s: round(random.gauss(self.config['symbols'][s]['mu'], self.config['symbols'][s]['sigma']), 4)
                for s in self.config['symbols']
            }
            print(self.current_quotes)
            time.sleep(1)

    def get_current_quote(self, symbol: Symbol) -> float:
        return self.current_quotes[symbol.name]


quote_generator = QuotesGenerator()
quote_generator.start()
