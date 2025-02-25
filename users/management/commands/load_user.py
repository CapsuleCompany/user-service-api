from django.core.management.base import BaseCommand
from django.conf import settings
from users.models import AuthUser, UserSettings, UserOrganization
import requests

UserSettings.objects.all().delete()
AuthUser.objects.all().delete()

TENANT_API_URL = settings.TENANT_API_URL


class Command(BaseCommand):
    help = "Creates a test user if DEBUG=True"

    def handle(self, *args, **kwargs):
        if not settings.DEBUG:
            self.stdout.write(
                self.style.ERROR("DEBUG mode is OFF. Skipping test user creation.")
            )
            return

        response = requests.get(TENANT_API_URL)
        data = response.json()
        if response.status_code != 200:
            self.stdout.write(
                self.style.ERROR(
                    f"Tenant API is not reachable. Status code: {response.status_code}"
                )
            )
            return

        if data == []:
            self.stdout.write(
                self.style.ERROR(f"Tenant API has no tenants: {response.status_code}")
            )
            return

        tenant = data[0]["id"]

        email = "ccrowder@capsuleio.com"
        phone_number = "9377230086"
        password = "test"
        full_name = "Camryn Crowder"

        if AuthUser.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f"User {email} already exists."))
            return

        user = AuthUser.objects.create(
            email=email,
            is_staff=True,
            is_superuser=True,
            username=email,
            phone_number=phone_number,
            first_name=full_name.split()[0],
            last_name=full_name.split()[-1],
            is_email_verified=True,
            is_phone_verified=True,
        )
        user.set_password(password)
        user.save()

        UserSettings.objects.create(user=user)

        org, created = UserOrganization.objects.get_or_create(
            user=user, tenant_id=tenant
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(f"User {email} added to organization {tenant}")
            )
        org.save()

        self.stdout.write(
            self.style.SUCCESS(f"Test user {email} created successfully!")
        )
