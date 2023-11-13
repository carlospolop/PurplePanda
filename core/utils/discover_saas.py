import time
import logging
from .purplepanda import PurplePanda
import core.utils.purplepanda


class DiscoverSaas(PurplePanda):
    logger = logging.getLogger(__name__)

    def __init__(self, initial_funcs, parallel_funcs, final_funcs=None):
        if final_funcs is None:
            final_funcs = []
        self.initial_funcs = initial_funcs
        self.parallel_funcs = parallel_funcs
        self.final_funcs = final_funcs

    def do_discovery(self):
        # Start running sequncially the initial functions
        for f in self.initial_funcs:
            self._call_f(f)

        # Then run in parallel the functions that can be parallelized (following the desired order inside each parallelism)
        threads = []
        for fs in self.parallel_funcs:
            future = core.utils.purplepanda.POOL.submit(self._do_parallel, fs)
            threads.append(future)

        # Show errors inside the threads
        for t in threads:
            t.result()

        while any(not t.done() for t in threads):
            time.sleep(5)

        # Call final functions (if any)
        for f in self.final_funcs:
            self._call_f(f)

    def _do_parallel(self, funcs: list):
        # Just call each function
        for f in funcs:
            self._call_f(f)

    def _call_f(self, func):
        if func:
            start = time.time()
            func()
            end = time.time()
            self.logger.debug(f"The function '{func}' took: {int(end - start)}")
