import unittest
from research.scripts.event_error_audit import summarize


class EventErrorTests(unittest.TestCase):
    def fixture(self):
        rows=[dict(id=str(i),label='CENTER',event='a' if i<2 else 'b',text_sha256=str(i),strict_agreement=True) for i in range(3)]
        predictions=[dict(id=str(i),gold='CENTER',prediction='LEFT' if i<2 else 'CENTER',text_sha256=str(i),fold=0 if i<2 else 1) for i in range(3)]
        return rows,predictions

    def test_counts_and_zero_error_case(self):
        rows,p=self.fixture()
        r=summarize(rows,p)
        self.assertEqual((r['errors'],r['center_errors'],r['events_with_center_errors']),(2,2,1))
        self.assertEqual(r['top_five_error_share'],1)
        for x in p: x['prediction']='CENTER'
        self.assertIsNone(summarize(rows,p)['top_five_error_share'])

    def test_duplicate_missing_and_mismatched_rows_rejected(self):
        rows,p=self.fixture()
        for bad in (p[:2],p+[p[0]],[dict(x,gold='RIGHT') for x in p]):
            with self.assertRaises(ValueError): summarize(rows,bad)

    def test_split_event_rejected(self):
        rows,p=self.fixture()
        p[0]['fold']=2
        with self.assertRaisesRegex(ValueError,'crosses'): summarize(rows,p)
