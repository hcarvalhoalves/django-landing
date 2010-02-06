About Landing
=============

Landing is a simple Django application for implementing A/B tests on your site.
It was heavily inspired by Vanity for Rails, but the implementation is vastly
different, better suited to how Django apps works.

It can be plugged right into any working Django project, and be used to track
visitor's conversions according to any aspect of your site. It also generates
reports on-the-fly for each experiment, easy to use by developers, designers
and management alike.


To setup Landing for you Django project
---------------------------------------

- Add to your installed apps on `settings.py`

::

    INSTALLED_APPS = (
        'django.contrib.sessions',
        ...
        'landing',
    )

Landing depends on `django.contrib.sessions`, so make sure it's there too.


- Add the URL routing for reports

::

    urlpatterns = patterns('',
        ...
        (r'^landing/', include('landing.urls')),
    )

You can also wrap the views in your own views, if you want to protect the
reports with login. Landing uses only 2 views: `list` and `report`.


To start using Landing on your project
--------------------------------------

- Register a new metric you want to track

At any module level code (I recommend the `views.py`):

::

    from landing import register_metric

    signup_options = ['simple', 'complete']
    signup_metric = register_metric('Signup', 'Test 2 signup forms',
                                    options=signup_options)


The metric could also, in theory, be loaded with fixtures or an admin.


- Decorate your views for tracking the metric

::

    @track(signup_metric)
    def my_view(request):
        if request.tracking:
            # Do something with tracking

If the `request.tracking` object is present, it means we were able to track
a visitor (cookies enabled), and also able to assign a random option to him.
It's present at `request.tracking.option`. For the next requests, this visitor
will consistently be assigned the same option (until, of course, cookies are
not valid anymore).

Your code can then branch accordingly to each option that was assigned. Some use
cases would include using different form classes, loading different templates,
or showing different pieces of a template. It all depends on the variables you
want to experiment with.

Once your visitor reaches a checkpoint in your view (e.g., signup done), you
track a conversion for it with:

::

    @track(signup_metric)
    def signup(request):
        ...
        if form.is_valid():
            request.tracking.track() # Record a conversion
            ...

That's it. From now on you can check the reports (if following this `README`,
it would be available at `/landing/`) and see how your experiment progresses.
It presents the conversion rates, the best option (with a confidence level of
at least 90%) and also a graph for conversions by period, so you can see how
conversions spread during the experiment period and quickly assess any biases.

As the experiment progresses and reaches to a conclusion, you can have your code
automaticaly select the optimal choice with something like:

::

    form_options = {'simple': SimpleForm, 'complete': CompleteForm}

    def signup_form(request):
        ...
        if signup_metric.choice(): # Best, statistical relevant option
            form_class = form_options.get(signup_metric.choice().value)
            ... # Proceed, now with the proven best form ;)


-----

You can learn more about A/B testing and the statistics involved at:
http://20bits.com/articles/hypothesis-testing-the-basics/

The original GitHub project page is at:
http://github.com/hcarvalhoalves/django-landing

About Vanity, our inspiration source:
http://vanity.labnotes.org/
