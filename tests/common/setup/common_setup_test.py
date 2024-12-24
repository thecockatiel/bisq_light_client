import asyncio 
import sys
import threading
import unittest
from bisq.common.setup.common_setup import CommonSetup
from bisq.common.user_thread import UserThread
from utils.test import run_with_reactor, teardown_reactor, twisted_wait

class MockExceptionHandler:
    def __init__(self):
        self.exception_caught = False
        
    def handle_uncaught_exception(self, exception, shutdown):
        self.exception_caught = True

def raise_error():
    raise Exception("Test unhandled error")

class TestExceptionHandler(unittest.TestCase):
    
    def tearDown(self):
        sys.excepthook = sys.__excepthook__
        threading.excepthook = threading.__excepthook__
        teardown_reactor()
    
    @run_with_reactor
    async def test_uncaught_exception_handler_for_user_thread_executed_methods(self):
        mock_handler = MockExceptionHandler()
        CommonSetup.setup_uncaught_exception_handler(mock_handler)

        await twisted_wait(0.5)

        e = asyncio.Event()
        
        timer = UserThread.execute(raise_error)
        
        await twisted_wait(0.1)
        
        timer._deferred.addBoth(lambda _: e.set())

        try:
            await asyncio.wait_for(e.wait(), 5)
            await twisted_wait(0.5)
        except asyncio.TimeoutError:
            self.fail("Test timed out waiting for exception handler")
        
        
        await twisted_wait(0.5)
            
        self.assertTrue(mock_handler.exception_caught)
        
    @run_with_reactor
    async def test_uncaught_exception_handler_for_threads(self):
        mock_handler = MockExceptionHandler()
        CommonSetup.setup_uncaught_exception_handler(mock_handler)

        def raise_exception():
            raise Exception("Test thread exception")
            
        thread = threading.Thread(target=raise_exception)
        thread.start()
        thread.join()
        
        await twisted_wait(0.5)
        
        self.assertTrue(mock_handler.exception_caught)

if __name__ == '__main__':
    unittest.main()