import unittest
import sys
import os

def run_tests():
    """Run all tests and generate a report"""
    loader = unittest.TestLoader()
    
    test_suite = loader.discover('./tests/', pattern='test_*.py')
    
    if os.path.exists('integration_tests.py'):
        integration_tests = loader.discover('./tests/', pattern='integration_tests.py')
        test_suite.addTests(integration_tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_tests())