import unittest
import sys

from tests.api.test_goal_probability_api import GoalProbabilityAPITest
from tests.api.test_visualization_integration import VisualizationDataAPITest
from tests.api.test_goal_api_v2 import GoalAPIV2Test

def create_api_test_suite():
    suite = unittest.TestSuite()
    
    # Add Goal Probability API tests
    suite.addTest(GoalProbabilityAPITest('test_01_get_goal_probability'))
    suite.addTest(GoalProbabilityAPITest('test_02_calculate_goal_probability'))
    # Add more tests as needed
    
    # Add Visualization Data API tests
    suite.addTest(VisualizationDataAPITest('test_01_visualization_data_structure'))
    # Add more tests as needed
    
    # Add Goal API V2 tests
    suite.addTest(GoalAPIV2Test('test_01_api_versioning_path'))
    # Add more tests as needed
    
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(create_api_test_suite())
    sys.exit(not result.wasSuccessful())
