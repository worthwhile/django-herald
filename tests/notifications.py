from email.mime.image import MIMEImage

from django.core.files import File

from herald import registry
from herald.base import EmailNotification
from herald.base import TwilioTextNotification


@registry.register
class MyNotification(EmailNotification):
    context = {"hello": "world"}
    template_name = "hello_world"
    to_emails = ["test@test.com"]

    def get_attachments(self):
        # this returns two attachments, one a text file, the other an inline attachment that can be referred to in a
        # template using cid: notation
        fp = open("tests/python.jpeg", "rb")
        img = MIMEImage(fp.read())
        img.add_header("Content-ID", "<{}>".format("python.jpg"))

        raw_data = "Some Report Data"

        fp.close()

        return [
            ("Report.txt", raw_data, "text/plain"),
            img,
        ]


@registry.register
class MyOtherNotification(EmailNotification):
    context = {"hello": "world"}
    template_name = "hello_world"
    to_emails = ["test@test.com"]


@registry.register
class MyTwilioNotification(TwilioTextNotification):
    context = {"hello": "world"}
    template_name = "hello_world"
    to_emails = ["test@test.com"]


@registry.register
class MyNotificationAttachmentOpen(EmailNotification):
    context = {"hello": "world"}
    template_name = "hello_world"
    to_emails = ["test@test.com"]

    def get_attachments(self):
        with open("tests/python.jpeg", "rb") as f:
            img = File(f)
        
        with open("tests/python.jpeg", "rb") as f:
            img2 = File(f)

        return [img, img2]
