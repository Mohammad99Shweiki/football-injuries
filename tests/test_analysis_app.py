"""Read-only app contracts and isolated approval checks; never touch the research data."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analysis import api


class AnalysisAppTests(unittest.TestCase):
    @unittest.skipUnless((api.RESULTS_DIR / "styles.json").exists(), "requires local Phase 6 outputs")
    def test_real_phase_and_results_contracts(self):
        status, _, body = api.handle('GET', '/api/analysis/phases', '', {})
        self.assertEqual(status, 200)
        phases = json.loads(body)
        self.assertEqual([p['id'] for p in phases], ['00', '01', '02', '03', '04', '05', '06'])
        self.assertTrue(all(p['steps'] for p in phases))
        status, _, body = api.handle('GET', '/api/analysis/results-bundle', '', {})
        self.assertEqual(status, 200)
        self.assertTrue({'styles', 'cluster_map', 'rr_ladder', 'season_trend'} <= json.loads(body).keys())

    def test_raw_and_traversal_downloads_rejected(self):
        for path in ('data/raw/example.csv', '../secret.csv', '/etc/passwd'):
            self.assertEqual(api.download({'path': [path]})[0], 400)

    def test_approval_requires_the_reviewed_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mapping = root / 'labels.csv'
            mapping.write_text('label,area\nstrain,muscle\n')
            (root / 'DECISIONS.md').write_text('# Decisions\n')
            with patch.object(api, 'MAPPINGS_DIR', root), patch.object(api, 'APPROVALS', root / 'approvals.json'), patch.object(api, 'DOCS', root):
                self.assertEqual(api.approve('labels.csv', {'hash': 'old-version'})[0], 409)
                self.assertFalse((root / 'approvals.json').exists())
                digest = hashlib.sha256(mapping.read_bytes()).hexdigest()[:16]
                self.assertEqual(api.approve('labels.csv', {'hash': digest})[0], 200)
                self.assertEqual(json.loads((root / 'approvals.json').read_text())['labels.csv']['hash'], digest)
                self.assertIn('approved', (root / 'DECISIONS.md').read_text())

    def test_scraping_blocks_analysis_without_starting_process(self):
        with patch.object(api.JOB, 'start') as start:
            self.assertEqual(api.handle('POST', '/api/analysis/run', '', {'phase': 'all'}, scrape_busy=True)[0], 409)
            start.assert_not_called()
        status, _, body = api.handle('GET', '/api/analysis/run', '', {}, scrape_busy=True)
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)['scrape_busy'])

    def test_paginated_table_and_csv_export(self):
        query = {'path': ['mappings/team_map.csv'], 'limit': ['2'], 'offset': ['0']}
        # Use the repository's actual mapping name instead of assuming one.
        query['path'] = [f'mappings/{next(api.MAPPINGS_DIR.glob("*.csv")).name}']
        status, _, body = api.table(query)
        self.assertEqual(status, 200)
        self.assertLessEqual(len(json.loads(body)['rows']), 2)
        status, kind, body = api.download(query)
        self.assertEqual(status, 200)
        self.assertTrue(kind.startswith('text/csv'))
        self.assertGreater(len(body.splitlines()), 2)


if __name__ == '__main__':
    unittest.main()
