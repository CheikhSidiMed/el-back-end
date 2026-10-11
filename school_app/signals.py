from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Competition, Tasfiya, Agent, Utilisateur, Job


# @receiver(post_save, sender=Competition)
# def create_default_tasfiyat(sender, instance, created, **kwargs):
#     if created:
#         for i in range(1, instance.number_of_tasfiyat + 1):
#             Tasfiya.objects.create(
#                 competition=instance,
#                 name=f"تصفية {i}",
#                 order=i
#             )
@receiver(post_save, sender=Competition)
def create_default_tasfiyat(sender, instance, created, **kwargs):
    if created:
        tasfiyat = [
            Tasfiya(
                competition=instance,
                name=f"تصفية {i}",
                order=i
            )
            for i in range(1, instance.number_of_tasfiyat + 1)
        ]
        Tasfiya.objects.bulk_create(tasfiyat)


@receiver(post_save, sender=Agent)
def create_agent_user_account(sender, instance, created, **kwargs):
    if not created:
        return

    raw_phone = instance.phone or ''
    # Strip country code prefix to get local number (e.g. 0022221212123 → 21212123)
    phone = raw_phone.lstrip('+')
    for prefix in ('00222', '222'):
        if phone.startswith(prefix):
            phone = phone[len(prefix):]
            break
    phone = phone.strip()

    if not phone:
        return

    agent_role, _ = Job.objects.get_or_create(title='agent', defaults={'description': 'وكيل'})

    # Check if a user with this local phone already exists
    existing = Utilisateur.objects.filter(phone=phone).first()
    if existing:
        existing.agent_profile = instance
        if existing.role is None:
            existing.role = agent_role
        else:
            existing.extra_roles.add(agent_role)
        existing.save()
        return

    # No existing user — create new account with the stripped local phone
    user = Utilisateur.objects.create_user(phone=phone, password=phone)
    user.first_name = instance.agent_name
    user.role = agent_role
    user.agent_profile = instance
    user.must_change_password = True
    user.save()
