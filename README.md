# django-herald

[![Latest PyPI version](https://badge.fury.io/py/django-herald.svg)](https://pypi.python.org/pypi/django-herald)
[![Build Status](https://travis-ci.org/worthwhile/django-herald.svg?branch=master)](https://travis-ci.org/worthwhile/django-herald)
[![Coverage Status](https://coveralls.io/repos/github/worthwhile/django-herald/badge.svg?branch=master)](https://coveralls.io/github/worthwhile/django-herald?branch=master)

[![Logo](https://github.com/worthwhile/django-herald/blob/master/logo.png)](https://github.com/worthwhile/django-herald)

Django library for separating the message content from transmission method

# Installation

1. `pip install django-herald`
2. Add `herald` and `django.contrib.sites` to `INSTALLED_APPS`.
3. Add herald's URLS:

        if settings.DEBUG:
            urlpatterns = [
                url(r'^herald/', include('herald.urls')),
            ] + urlpatterns

# Usage

1. Create a `notifications.py` file in any django app. This is where your notification classes will live. Add a class like this:

        from herald import registry
        from herald.base import EmailNotification


        class WelcomeEmail(EmailNotification):  # extend from EmailNotification for emails
           template_name = 'welcome_email'  # name of template, without extension
           subject = 'Welcome'  # subject of email

           def __init__(self, user):  # optionally customize the initialization
               self.context = {'user': user}  # set context for the template rendering
               self.to_emails = [user.email]  # set list of emails to send to

           @staticmethod
           def get_demo_args():  # define a static method to return list of args needed to initialize class for testing
               from users.models import User
               return [User.objects.order_by('?')[0]]

        registry.register(WelcomeEmail)  # finally, register your notification class

        # Alternatively, a class decorator can be used to register the notification:

        @registry.register_decorator()
        class WelcomeEmail(EmailNotification):
            ...


2. Create templates for rendering the email using this file structure:

        templates/
            herald/
                text/
                    welcome_email.txt
                html/
                    welcome_email.html

3. Test how your email looks by navigating to `/herald/`.

4. Send your email wherever you need in your code:

        WelcomeEmail(user).send()

5. View the sent emails in django admin and even be able to resend it.


## Deleting Old Notifications

The `delnotifs` command is useful for purging the notification history.

The default usage will delete everything from sent during today:

    python manage.py delnotifs

However, you can also pass arguments for `start` or `end` dates. `end` is up to, but not including that date.

    python manage.py delnotifs --start='2016-01-01' --end='2016-01-10'


## Asynchronous Email Sending

If you are sending slightly different emails to a large number of people, it might take quite a while to process. By default, Django will process this all synchronously. For asynchronous support, we recommend django-celery-email. It is very straightfoward to setup and integrate: https://github.com/pmclanahan/django-celery-email


## herald.contrib.auth

Django has built-in support for sending password reset emails. If you would like to send those emails using herald, you can use the notification class in herald.contrib.auth.

First, add `herald.contrib.auth` to `INSTALLED_APPS` (in addition to `herald`).

Second, use the `HeraldPasswordResetForm` in place of django's built in `PasswordResetForm`. This step is entirely dependant on your project structure, but it essentially just involves changing the form class on the password reset view in some way:

    # you may simply just need to override the password reset url like so:
    url(r'^password_reset/$', password_reset, name='password_reset', {'password_reset_form': HeraldPasswordResetForm}),

    # of if you are using something like django-authtools:
    url(r'^password_reset/$', PasswordResetView.as_view(form_class=HeraldPasswordResetForm), name='password_reset'),

    # or you may have a customized version of the password reset view:
    class MyPasswordResetView(FormView):
        form_class = HeraldPasswordResetForm  # change the form class here

    # or, you may have a custom password reset form already. In that case, you will want to extend from the HeraldPasswordResetForm:
    class MyPasswordResetForm(HeraldPasswordResetForm):
        ...

    # alternatively, you could even just send the notification wherever you wish, seperate from the form:
    PasswordResetEmail(some_user).send()

Third, you may want to customize the templates for the email. By default, herald will use the `registration/password_reset_email.html` that is provided by django for both the html and text versions of the email. But you can simply override `herald/html/password_reset.html` and/or `herald/text/password_reset.txt` to suit your needs.

## User Disabled Notifications

If you want to disable certain notifications per user, add a record to the UserNotification table and
add notifications to the disabled_notifications many to many table.

For example:

        user = User.objects.get(id=user.id)

        notification = Notification.objects.get(notification_class='MyNotification')

        # disable the notification
        user.usernotification.disabled_notifications.add(notification)

By default, notifications can be disabled.  You can put can_disable = False in your notification class and the system will
populate the database with this default.  Your Notification class can also override the verbose_name by setting it in your
inherited Notification class.  Like this:

    class MyNotification(EmailNotification):
        can_disable = False
        verbose_name = "My Required Notification"

## Email Attachments

To send attachments, assign a list of attachments to the attachments attribute of your EmailNotification instance, or override the get_attachments() method.

Each attachment in the list can be one of the following:

1. A tuple which consists of the filename, the raw attachment data, and the mimetype. It is up to you to get the attachment data. Like this:

        raw_data = get_pdf_data()

        email.attachments = [
           ('Report.pdf', raw_data, 'application/pdf'),
           ('report.txt', 'text version of report', 'text/plain')
        ]
        email.send()

2. A MIMEBase object. See the documentation for attachments under EmailMessage Objects/attachments in the Django documentation.

3. A django `File` object.

### Inline Attachments

Sometimes you want to embed an image directly into the email content.  Do that by using a MIMEImage assigning a content id header to a MIMEImage, like this:

    email = WelcomeEmail(user)
    im = get_thumbnail(image_file.name, '600x600', quality=95)
    my_image = MIMEImage(im.read()) # MIMEImage inherits from MIMEBase
    my_image.add_header('Content-ID', '<{}>'.format(image_file.name))

You can refer to these images in your html email templates using the Content ID (cid) like this:

    <img src="cid:{{image_file.name}}" />
    
You would of course need to add the "image_file" to your template context in the example above.  You can also accomplish this using file operations.  In this example we overrode the get_attachments method of an EmailNotification.

    class MyNotification(EmailNotification):
        context = {'hello': 'world'}
        template_name = 'welcome_email'
        to_emails = ['somebody@example.com']
        subject = "My email test"
            
        def get_attachments(self):
            fp = open('python.jpeg', 'rb')
            img = MIMEImage(fp.read())
            img.add_header('Content-ID', '<{}>'.format('python.jpeg'))
            return [
                img,
            ]

And in your template you would refer to it like this, and you would not need to add anything to the context:

    <img src="cid:python.jpeg" />

### Other MIME attachments

You can also attach any MIMEBase objects as regular attachments, but you must add a content-disposition header, or they will be inaccessible:  

    my_image.add_header('Content-Disposition', 'attachment; filename="python.jpg"')

Attachments can cause your database to become quite large, so you should be sure to run the management commands to purge the database of old messages.

# Running Tests

    python runtests.py
