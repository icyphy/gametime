import unittest
import pulp


class MyTestCase(unittest.TestCase):
    def test_pulp_valid(self):
        print(pulp.list_solvers(True))
        print(pulp.list_solvers(False))


if __name__ == '__main__':
    unittest.main()
