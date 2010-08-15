from django.utils.hashcompat import md5_constructor
from landing.models import Metric, Option, TrackRecord
from time import time

RECORD_HASH_PREFIX = 'landing_h_'

def register_metric(name, description='', options=None):
    """
    A helper for setting and getting a `Metric` programatically. You can keep a
    call for this in views.py, and use with the decorator like this:

    ```
    signup_options = ['simple', 'complete']
    signup_metric = register_metric('Signup', 'Test 2 signup forms',
                                    options=signup_options)

    @track(signup_metric)
    def my_view(request):
        if request.tracking:
            # Do something with tracking

    ```

    Other ways to add metrics include loading fixtures or via the admin, but
    this method is preferable if you want to keep the experiments in the
    source code for version control, or want more flexibility.
    """
    metric, created = Metric.objects.get_or_create(name=name,
                                                   description=description)
    if not created:
        return metric

    for value in options:
        option, created = Option.objects.get_or_create(metric=metric,
                                                       value=unicode(value))
        if created:
            metric.option_set.add(option)

    return metric


class Tracking(object):
    """
    Tracks chosen metrics, options and conversions, and keep the data
    available on the request object.
    """
    def __init__(self, request, metric):
        self.metric = metric

        # Keys are kept unique for each metric
        self.RECORD_HASH_KEY = RECORD_HASH_PREFIX + str(metric.pk)
        record_hash = request.session.get(self.RECORD_HASH_KEY, None)

        # New visitor, select a new hash and option        
        if not record_hash:
            self.record = self._set_record(metric)
            return True
            
        # Returning visitor
        self.record = self._get_record(record_hash)
        return False

    def __unicode__(self):
        return "[%s] %s for %s" % (self.metric, self.option, self.hash)

    def _set_record(self, metric):
        option = metric.get_random_option()
        record = TrackRecord.objects.create(option=option)
        return record

    def _get_record(self, hash):
        try:
            return TrackRecord.objects.get(hash=hash)
        except Option.DoesNotExist:
            return None

    @property
    def hash(self):
        return self.record.hash

    @property
    def option(self):
        return self.record.option

    def setup_session(self, request):
        # This metric isn't valid, forget about this session
        if not self.record:
            try:
                del request.session[self.RECORD_HASH_KEY]
            except KeyError:
                pass
        else:
            request.session[self.RECORD_HASH_KEY] = self.record.hash
        return request

    def track(self):
        """
        Track a conversion. Call this once your visitor arrives successfully
        to a certain checkpoint (e.g.: a signup form conclusion).
        """
        return self.record.track_conversion()
