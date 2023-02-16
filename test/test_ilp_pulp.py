import unittest
import pulp


class MyTestCase(unittest.TestCase):
    def test_pulp_valid(self):
        print(pulp.listSolvers(True))
        print(pulp.listSolvers(False))


if __name__ == '__main__':
    unittest.main()
