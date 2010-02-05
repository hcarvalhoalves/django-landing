from landing import Tracking

class track(object):
    """
    Decorate a view to track information about a metric. The tracking object
    will be available at `request.tracking` (but only if metric is enabled and
    session is valid).

    The `metric` argument is what you want to track. It can be either a
    `Metric` instance, or a callable that returns one.
    """
    def __init__(self, metric):
        if callable(metric):
            metric = metric()
        self.metric = metric

    def __call__(self, f):
        def _add_tracking(request, *args, **kwargs):
            request = self.track_request(request)
            return f(request, *args, **kwargs)
        return _add_tracking

    def track_request(self, request):
        if self.metric.enabled:
            tracking = Tracking(request, self.metric)
            if not tracking.setup:
                request = tracking.setup_session(request)
            request.tracking = tracking
        return request
