import unittest
from refresh_jobs import categorize, level

class MatchingTests(unittest.TestCase):
    def test_all_requested_paths_have_matching_alias(self):
        from refresh_jobs import ROLES
        self.assertEqual(len(ROLES), 30)
        for index, role in enumerate(ROLES):
            self.assertIn(index, categorize(role[3][0]))

    def test_senior_title_never_mislabeled_as_entry(self):
        self.assertEqual(level('Senior Associate Data Analyst'), 'experienced')
        self.assertEqual(level('Staff Software Engineer'), 'experienced')
        self.assertEqual(level('Junior Data Analyst'), 'entry')
        self.assertEqual(level('Data Analyst'), 'unspecified')
        self.assertEqual(level('Analyst', {'id': 'entry_level'}), 'entry')

    def test_unrelated_roles_are_not_promoted_to_candidates(self):
        self.assertEqual(categorize('Executive Chef'), [])
        self.assertEqual(categorize('Luxury Hotel Chef'), [])
        self.assertEqual(categorize('People Help Desk Analyst'), [])
        self.assertEqual(categorize('Purchasing Project Management'), [])
        self.assertIn(17, categorize('Junior Data Analyst'))
        self.assertIn(0, categorize('Business Analyst'))

if __name__ == '__main__':
    unittest.main()
