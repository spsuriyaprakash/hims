from django.core.management.base import BaseCommand
from django.db import transaction

from identity.models import (
    ApiPermission,
    Application,
    Facility,
    Role,
    RolePermission,
    User,
    UserFacility,
    UserIdentity,
)

REALM_ROLES = [
    ("super_admin", "Super Admin"),
    ("hospital_admin", "Hospital Admin"),
    ("doctor", "Doctor"),
    ("nurse", "Nurse"),
    ("receptionist", "Receptionist"),
    ("lab_technician", "Lab Technician"),
    ("pharmacist", "Pharmacist"),
    ("billing_clerk", "Billing Clerk"),
    ("auditor", "Auditor"),
]

PERMISSIONS = [
    ("patient.read", "Read patient", "GET", "patient"),
    ("patient.create", "Create patient", "POST", "patient"),
    ("patient.update", "Update patient", "PATCH", "patient"),
    ("appointment.read", "Read appointment", "GET", "appointment"),
    ("appointment.create", "Create appointment", "POST", "appointment"),
    ("appointment.cancel", "Cancel appointment", "POST", "appointment"),
    ("encounter.read", "Read encounter", "GET", "encounter"),
    ("encounter.create", "Create encounter", "POST", "encounter"),
    ("encounter.update", "Update encounter", "PATCH", "encounter"),
    ("note.create", "Create clinical note", "POST", "note"),
    ("prescription.create", "Create prescription", "POST", "prescription"),
    ("billing.read", "Read billing", "GET", "billing"),
    ("billing.refund", "Refund billing", "POST", "billing"),
    ("admin.configure", "Configure system", "PATCH", "admin"),
]

ROLE_PERMISSIONS = {
    "super_admin": [code for code, *_ in PERMISSIONS],
    "hospital_admin": [
        "patient.read",
        "patient.create",
        "patient.update",
        "appointment.read",
        "appointment.create",
        "appointment.cancel",
        "encounter.read",
        "billing.read",
        "billing.refund",
        "admin.configure",
    ],
    "doctor": [
        "patient.read",
        "appointment.read",
        "encounter.read",
        "encounter.create",
        "encounter.update",
        "note.create",
        "prescription.create",
    ],
    "nurse": [
        "patient.read",
        "appointment.read",
        "encounter.read",
        "encounter.create",
        "note.create",
    ],
    "receptionist": [
        "patient.read",
        "patient.create",
        "patient.update",
        "appointment.read",
        "appointment.create",
        "appointment.cancel",
        "billing.read",
    ],
    "billing_clerk": ["patient.read", "billing.read", "billing.refund"],
    "auditor": ["patient.read", "appointment.read", "encounter.read", "billing.read"],
    "lab_technician": ["patient.read", "encounter.read"],
    "pharmacist": ["patient.read", "prescription.create"],
}

ANITA_SUB = "8f1c2a10-6b3e-4c1a-9d44-111111111111"


class Command(BaseCommand):
    help = "Seed application, role, permission, and facility catalog data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--demo-user",
            action="store_true",
            help="Create Dr. Anita local identity (same sub as Keycloak import).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        hims_api, _ = Application.objects.update_or_create(
            code="hims-api",
            defaults={
                "name": "HIMS API",
                "keycloak_client_id": "hims-api",
                "app_kind": Application.Kind.API,
                "base_url": "http://localhost:8000",
                "is_active": True,
            },
        )
        Application.objects.update_or_create(
            code="hims-web",
            defaults={
                "name": "HIMS Web",
                "keycloak_client_id": "hims-web",
                "app_kind": Application.Kind.WEB,
                "base_url": "http://localhost:3000",
                "is_active": True,
            },
        )
        Application.objects.update_or_create(
            code="lab-api",
            defaults={
                "name": "Laboratory API",
                "keycloak_client_id": "lab-api",
                "app_kind": Application.Kind.API,
                "base_url": "http://localhost:8081",
                "is_active": True,
            },
        )

        main, _ = Facility.objects.update_or_create(
            code="FAC-001",
            defaults={"name": "Main Campus", "is_active": True},
        )
        annex, _ = Facility.objects.update_or_create(
            code="FAC-002",
            defaults={"name": "Annex Clinic", "is_active": True},
        )

        roles = {}
        for code, name in REALM_ROLES:
            role, _ = Role.objects.update_or_create(
                code=code,
                application=None,
                defaults={
                    "name": name,
                    "source": Role.Source.REALM,
                    "is_active": True,
                },
            )
            roles[code] = role

        permissions = {}
        for code, name, method, resource in PERMISSIONS:
            perm, _ = ApiPermission.objects.update_or_create(
                application=hims_api,
                code=code,
                defaults={
                    "name": name,
                    "http_method": method,
                    "resource": resource,
                    "is_active": True,
                },
            )
            permissions[code] = perm

        for role_code, perm_codes in ROLE_PERMISSIONS.items():
            role = roles[role_code]
            for perm_code in perm_codes:
                RolePermission.objects.get_or_create(
                    role=role,
                    permission=permissions[perm_code],
                )

        if options["demo_user"]:
            user, created = User.objects.get_or_create(
                username="anita.rao",
                defaults={
                    "email": "anita.rao@hospital.org",
                    "first_name": "Anita",
                    "last_name": "Rao",
                },
            )
            if created:
                user.set_unusable_password()
                user.save(update_fields=["password"])
            identity, _ = UserIdentity.objects.update_or_create(
                keycloak_sub=ANITA_SUB,
                defaults={
                    "user": user,
                    "username": "anita.rao",
                    "email": "anita.rao@hospital.org",
                    "full_name": "Dr. Anita Rao",
                    "employee_code": "EMP-1001",
                    "is_active": True,
                },
            )
            UserFacility.objects.get_or_create(
                user_identity=identity,
                facility=main,
                defaults={"is_primary": True, "is_active": True},
            )
            UserFacility.objects.get_or_create(
                user_identity=identity,
                facility=annex,
                defaults={"is_primary": False, "is_active": True},
            )
            self.stdout.write(self.style.SUCCESS("Demo user Anita seeded."))

        self.stdout.write(self.style.SUCCESS("Identity catalog seeded."))
