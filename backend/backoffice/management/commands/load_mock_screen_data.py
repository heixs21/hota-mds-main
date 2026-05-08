from django.core.management.base import BaseCommand

from backoffice.display_services import load_mock_display_data


class Command(BaseCommand):
    help = "Load M3 mock screen snapshots and data source health records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--simulate-failure",
            action="store_true",
            help="Mark sources as failed while keeping the last successful snapshots.",
        )

    def handle(self, *args, **options):
        result = load_mock_display_data(simulate_failure=options["simulate_failure"])
        mode = result["mode"]
        if mode == "failure":
            self.stdout.write(self.style.WARNING("mock screen data marked as failed; last successful snapshots retained"))
            self.stdout.write(self.style.WARNING(f"health records updated: {result['healthCount']}"))
            return

        self.stdout.write(self.style.SUCCESS("mock screen data loaded"))
        self.stdout.write(self.style.SUCCESS(f"generatedAt: {result['generatedAt']}"))
