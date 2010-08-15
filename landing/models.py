from django.db import models
from django.db.models import permalink
from datetime import datetime, timedelta
from uuid import uuid4

Z_SCORES = {2.75: 99.9, 2.26: 99, 1.63: 95, 1.27: 90}
GRAPH_TIMESLICES = 6

class Metric(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ('enabled', 'name')

    def __unicode__(self):
        return self.name

    @permalink
    def get_absolute_url(self):
        return ('landing.views.report', [str(self.pk)])

    def get_random_option(self):
        return self.option_set.order_by('?')[0]

    @property
    def participants(self):
        return sum(o.participants for o in self.option_set.all())

    @property
    def conversions(self):
        return sum(o.conversions for o in self.option_set.all())

    def sorted(self):
        return sorted(self.option_set.all(), key=lambda o:o.conversion_rate)

    @property
    def base(self):
        return self.sorted()[0]

    def best(self):
        """Best performant option so far"""
        return max(self.option_set.all(), key=lambda o:o.conversion_rate)

    def choice(self):
        """Best choice with statistical significance"""
        if self.best().probability:
            return self.best()
        return None

    def _data_by_timeslice(self, strftime, **kwargs):
        datasets, data, labels, legends = [], [], [], []

        for o in self.sorted():
            results, ranges = o.get_records_by_timeslice(**kwargs)
            dataset = [r.filter(converted=True).count() for r in results]
            labels = [r.strftime(strftime) for r in ranges]
            
            datasets.append(dataset)
            data.append(",".join([str(i) for i in dataset]))
            legends.append("%s" % o)
        
        max_axis = max((reduce(lambda a,b: a+b, t) for t in zip(*datasets)))

        return {'data': "|".join(data),
                'labels': "|".join(labels),
                'legends': "|".join(legends),
                'max': max_axis * 1.2}

    def chart(self):
        timeframe = self.base.timeframe()
        seconds = timeframe.seconds / GRAPH_TIMESLICES
        return self._data_by_timeslice("%x %X", seconds=seconds)


class Option(models.Model):
    metric = models.ForeignKey(Metric)
    value = models.CharField(max_length=255, unique=True)

    def __unicode__(self):
        return u"Option %s" % chr(self._rel_index() + 65)

    def _rel_index(self):
        return list(self.metric.option_set.all()).index(self)

    def get_first_record(self):
        return self.trackrecord_set.all()[0].timestamp

    def get_last_record(self):
        return self.trackrecord_set.reverse()[0].timestamp

    def timeframe(self):
        return self.get_last_record() - self.get_first_record()

    def get_records_by_timeslice(self, seconds=None):
        assert seconds > 0
        results, ranges = [], []
        qs = self.trackrecord_set.all()
        start = self.get_first_record()
        rng = self.timeframe().seconds / seconds
        rng = rng + 1 if rng % 2 else rng
        for d in xrange(rng):
            end = start + timedelta(seconds=seconds)
            results.append(qs.filter(timestamp__range=[start, end]))
            ranges.append(start)
            start = end
        return results, ranges

    @property
    def participants(self):
        return self.trackrecord_set.count()

    @property
    def conversions(self):
        return self.trackrecord_set.filter(converted=True).count()

    @property
    def conversion_rate(self):
        if self.participants > 1:
            return float(self.conversions) / float(self.participants)
        return 0.0

    @property
    def conversion_percent(self):
        return self.conversion_rate * 100.0

    @property
    def relative_conversion_percent(self):
        return (self.conversion_percent / self.metric.base.conversion_rate) - 100.0

    @property
    def std_deviation(self):
        pc = self.metric.base.conversions
        nc = self.metric.participants
        p = self.conversions
        n = self.participants
        return abs((p * (1-p)/n) + (pc * (1-pc)/nc)) ** 0.5

    @property
    def z_score(self):
        pc = self.metric.base.conversions
        p = self.conversions
        d = self.std_deviation
        return (p - pc) / d

    @property
    def probability(self):
        try:
            return [i[1] for i in Z_SCORES.items() if self.z_score >= i[0]][0]
        # Only whitin 90% probability matters
        except IndexError:
            return 0.0


class TrackRecord(models.Model):
    hash = models.CharField(max_length=32, primary_key=True)
    option = models.ForeignKey(Option)
    timestamp = models.DateTimeField(auto_now_add=True)
    converted = models.BooleanField()

    class Meta:
        ordering = ('timestamp',)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.hash = uuid4().hex
        super(TrackRecord, self).save(*args, **kwargs)
        
    def __unicode__(self):
        return u"[%s] %s for %s (%s)" % (self.option.metric, self.option,
                                         self.hash, self.timestamp)

    def track_conversion(self):
        self.converted = True
        return self.save()
