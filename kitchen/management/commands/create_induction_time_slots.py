from django.core.management.base import BaseCommand
from kitchen.models import InductionTimeSlot


class Command(BaseCommand):
    help = "앞으로 7일간의 시간 슬롯을 생성합니다"

    def add_arguments(self, parser):
        parser.add_argument("days", type=int)

    def handle(self, *args, **options):
        days = options["days"]
        InductionTimeSlot.create_time_slots(days=days)
        self.stdout.write(self.style.SUCCESS(f"앞으로 {days}일 시간 슬롯 생성 완료"))
