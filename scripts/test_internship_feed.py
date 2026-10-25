import unittest
from update_internships import normalize, is_internship, province_for

class InternshipFeedTests(unittest.TestCase):
    def test_internship_evidence(self):
        self.assertTrue(is_internship('Data Analyst Intern'))
        self.assertTrue(is_internship('นักศึกษาฝึกงาน การตลาด'))
        self.assertFalse(is_internship('International Sales Manager'))
        self.assertFalse(is_internship('Management Trainee'))
        self.assertTrue(is_internship('Food and Beverage', 'Internship'))

    def test_only_declared_thai_location_counts(self):
        source = ('sertis', 'Sertis', 'greenhouse')
        row = {'id': 1, 'title': 'Data Analyst Intern', 'location': {'name': 'Singapore'},
               'content': 'Our Thailand team', 'absolute_url': 'https://company.test/jobs/1'}
        self.assertIsNone(normalize(source, row, '2026-10-25T00:00:00Z'))
        row['location']['name'] = 'Bangkok, Thailand'
        result = normalize(source, row, '2026-10-25T00:00:00Z')
        self.assertEqual(result['province'], 'กรุงเทพมหานคร')
        row['application_deadline'] = '2026-10-20T00:00:00Z'
        self.assertIsNone(normalize(source, row, '2026-10-25T00:00:00Z'))

    def test_smartrecruiters_country_and_role(self):
        source = ('BoschGroup', 'Bosch', 'smartrecruiters')
        row = {'id': 2, 'name': 'Marketing Intern', 'location': {'country': 'vn', 'region': 'Bangkok'}}
        self.assertIsNone(normalize(source, row, '2026-10-25T00:00:00Z'))
        row['location'] = {'country': 'th', 'region': 'RAYONG', 'city': 'Factory'}
        self.assertEqual(normalize(source, row, '2026-10-25T00:00:00Z')['province'], 'ระยอง')
        row['name'] = 'Marketing Manager'
        self.assertIsNone(normalize(source, row, '2026-10-25T00:00:00Z'))
        row['name'] = 'Internship 2025 Marketing'
        self.assertIsNone(normalize(source, row, '2026-10-25T00:00:00Z'))

    def test_unknown_province_is_not_guessed(self):
        self.assertEqual(province_for('Thailand, Remote'), '')
        self.assertEqual(province_for('Phuket, PHUKET, Thailand'), 'ภูเก็ต')

if __name__ == '__main__':
    unittest.main()
