from django.utils.hashcompat import md5_constructor
from landing.models import Metric, Option, TrackRecord

SESSION_HASH = 'tracking_h_'
SESSION_OPTION = 'tracking_o_'

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
    An object to keep metric data and conversion available to the request. Also
    knows how to setup a session for itself.
    """
    def __init__(self, request, metric):
        self.metric = metric

        # Keys are kept unique for each metric
        self.METRIC_HASH = SESSION_HASH + str(metric.pk)
        self.METRIC_OPTION = SESSION_OPTION + str(metric.pk)

        # This is going to be pretty unique, but still reproducible.
        if not request.session.get(self.METRIC_HASH):
            uniqueness = request.META.get('REMOTE_ADDR') + \
                         request.META.get('HTTP_USER_AGENT') + \
                         request.META.get('HTTP_REFERER', '')
            self.hash = md5_constructor(uniqueness).hexdigest()
            self.option = self.metric.get_random_option()
            self.setup = False

        # Returning visitor
        else:
            self.hash = request.session[self.METRIC_HASH]
            self.option = self._recover_option(request.session[self.METRIC_OPTION])
            self.setup = True

        # Record a new participant
        self._record()

    def __unicode__(self):
        return "[%s] %s for %s" % (self.metric, self.option, self.hash)

    def _recover_option(self, pk):
        try:
            return Option.objects.get(pk=pk)
        except Option.DoesNotExist:
            return None

    def _record(self):
        record, created = TrackRecord.objects.get_or_create(hash=self.hash,
                                                            option=self.option)
        self.record = record
        return created

    def setup_session(self, request):
        # This metric isn't valid anymore, forget about this session
        if not self.option:
            del request.session[self.METRIC_HASH]
            del request.session[self.METRIC_OPTION]
        else:
            request.session[self.METRIC_HASH] = self.hash
            request.session[self.METRIC_OPTION] = self.option.pk
        return request

    def track(self):
        """
        Record a conversion. Call this once your visitor arrives successfully
        to a certain checkpoint (e.g.: a signup form conclusion).
        """
        return self.record.track_conversion()
