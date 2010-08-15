from django.test import TestCase
from landing import register_metric, Tracking
from landing.models import Metric, Option, TrackRecord


class MetricTest(TestCase):

    def setUp(self):
        self.metric = register_metric('Button Color Influence',
                                      'Check what users click more.',
                                      ['banana green', 'golden blue'])

    def test_track_conversions(self):
        for n in xrange(20):
            option = self.metric.get_random_option()
            record = TrackRecord.objects.create(option=option)
            if n % 2:
                record.track_conversion()

        self.assertEqual(self.metric.participants, 20)
        self.assertEqual(self.metric.conversions, 10)