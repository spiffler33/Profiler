import unittest
import logging
import sys

# Create a logger for detailed test information
logging.basicConfig(level=logging.DEBUG, filename='api_test_debug.log', filemode='w',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

logger = logging.getLogger('api_test_fix')

def run_diagnostic_test(module_name, test_name):
    """Run a single test with detailed diagnostic information"""
    try:
        # Add the current directory to sys.path to make imports work
        import os
        sys.path.insert(0, os.getcwd())
        
        # Dynamically import the test module and class
        module = __import__(f'tests.api.{module_name}', fromlist=['*'])
        
        # Get all test classes from the module
        test_classes = [cls for name, cls in module.__dict__.items() 
                     if isinstance(cls, type) and issubclass(cls, unittest.TestCase) and cls != unittest.TestCase]
        
        if not test_classes:
            logger.error(f"No test classes found in module {module_name}")
            return False
            
        test_class = test_classes[0]  # Take the first test class found
        logger.info(f"Running test {test_name} from {test_class.__name__}")
        
        # Create and run the test
        suite = unittest.TestSuite()
        suite.addTest(test_class(test_name))
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
    except Exception as e:
        logger.exception(f"Error running test {module_name}.{test_name}: {str(e)}")
        return False

def main():
    if len(sys.argv) < 3:
        print("Usage: python api_test_diagnostic.py <module_name> <test_name>")
        print("Example: python api_test_diagnostic.py test_goal_probability_api test_01_get_goal_probability")
        return 1
        
    module_name = sys.argv[1]
    test_name = sys.argv[2]
    
    success = run_diagnostic_test(module_name, test_name)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
