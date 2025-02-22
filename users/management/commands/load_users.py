from django.core.management.base import BaseCommand
from django.conf import settings
from users.models import AuthUser, UserSettings, UserOrganization
import random


class Command(BaseCommand):
    help = "Creates random test users from anime names"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=50,
            help="Specify the number of users to create",
        )

    def handle(self, *args, **kwargs):
        if not settings.DEBUG:
            self.stdout.write(
                self.style.ERROR("DEBUG mode is OFF. Skipping test user creation.")
            )
            return

        user_count = kwargs["count"]

        anime_names = [
            "Goku",
            "Vegeta",
            "Gohan",
            "Piccolo",
            "Trunks",
            "Bulma",
            "Frieza",
            "Krillin",
            "Cell",
            "Android 18",
            "Naruto Uzumaki",
            "Sasuke Uchiha",
            "Sakura Haruno",
            "Kakashi Hatake",
            "Itachi Uchiha",
            "Hinata Hyuga",
            "Gaara",
            "Jiraiya",
            "Rock Lee",
            "Shikamaru Nara",
            "Ichigo Kurosaki",
            "Rukia Kuchiki",
            "Uryu Ishida",
            "Orihime Inoue",
            "Renji Abarai",
            "Byakuya Kuchiki",
            "Toshiro Hitsugaya",
            "Kenpachi Zaraki",
            "Sosuke Aizen",
            "Yoruichi Shihoin",
            "Monkey D. Luffy",
            "Roronoa Zoro",
            "Nami",
            "Sanji",
            "Usopp",
            "Tony Tony Chopper",
            "Nico Robin",
            "Franky",
            "Brook",
            "Shanks",
        ]

        domains = ["example.com", "anime.com", "test.com"]

        # Delete previously created test users
        test_users = AuthUser.objects.filter(
            email__regex=r"^(goku|vegeta|gohan|piccolo|trunks|bulma|frieza|krillin|cell|android|naruto|sasuke|sakura|kakashi|itachi|hinata|gaara|jiraiya|rock|shikamaru|ichigo|rukia|uryu|orihime|renji|byakuya|toshiro|kenpachi|sosuke|yoruichi|monkey|roronoa|nami|sanji|usopp|tony|nico|franky|brook|shanks)\d+@.*"
        )
        test_users.delete()
        self.stdout.write(self.style.WARNING("Previous test users deleted."))

        admin_user = AuthUser.objects.filter(email="ccrowder@capsuleio.com").first()
        if not admin_user:
            self.stdout.write(
                self.style.WARNING("Admin user ccrowder@capsuleio.com does not exist.")
            )
            return

        admin_org = UserOrganization.objects.filter(user=admin_user).first()
        if not admin_org:
            self.stdout.write(
                self.style.WARNING(
                    "Admin user is not associated with any organization."
                )
            )
            return

        created_count = 0
        while created_count < user_count:
            full_name = random.choice(anime_names)
            first_name = full_name.split()[0]
            last_name = full_name.split()[-1] if len(full_name.split()) > 1 else "User"
            email = (
                f"{first_name.lower()}{random.randint(1,1000)}@{random.choice(domains)}"
            )
            phone_number = f"555{random.randint(1000000, 9999999)}"
            password = "test123"

            if AuthUser.objects.filter(email=email).exists():
                continue

            user = AuthUser.objects.create(
                email=email,
                username=email,
                phone_number=phone_number,
                first_name=first_name,
                last_name=last_name,
                is_email_verified=True,
                is_phone_verified=True,
            )
            user.set_password(password)
            user.save()

            UserSettings.objects.create(user=user)
            UserOrganization.objects.create(
                user=user, tenant_id=admin_org.tenant_id, role=admin_org.role
            )

            created_count += 1
            self.stdout.write(self.style.SUCCESS(f"User {email} created."))

        self.stdout.write(
            self.style.SUCCESS(f"{user_count} random test users created successfully!")
        )
