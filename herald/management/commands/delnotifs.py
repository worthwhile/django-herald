import datetime

from django.utils import timezone
from django.core.management.base import BaseCommand

from ...models import SentNotification


def valid_date(s):
    return datetime.datetime.strptime(s, "%Y-%m-%d")


class Command(BaseCommand):
    help = "Deletes notifications between the date ranges specified."

    def add_arguments(self, parser):
        parser.add_argument(
            "--start", help="includes this date, format YYYY-MM-DD", type=valid_date
        )
        parser.add_argument(
            "--end", help="up to this date, format YYYY-MM-DD", type=valid_date
        )

    def handle(self, *args, **options):
        start_date = options.get("start")
        end_date = options.get("end")

        if not start_date and not end_date:
            qs = SentNotification.objects.filter(date_sent__date=timezone.localdate())
        else:
            today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            date_filters = {
                "date_sent__lt": end_date or (today + datetime.timedelta(days=1))
            }
            if start_date:
                date_filters["date_sent__gte"] = start_date
            qs = SentNotification.objects.filter(**date_filters)

        present_notifications = qs.count()
        deleted_notifications = qs.delete()
        deleted_num = (
            deleted_notifications[0]
            if deleted_notifications is not None
            else present_notifications
        )
        self.stdout.write(
            "Successfully deleted {num} notification(s)".format(num=deleted_num)
        )
