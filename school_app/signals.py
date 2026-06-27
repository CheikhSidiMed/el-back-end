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
    phone = instance.phone
    if not phone:
        return
    if Utilisateur.objects.filter(phone=phone).exists():
        return
    agent_role, _ = Job.objects.get_or_create(title='agent', defaults={'description': 'وكيل'})
    user = Utilisateur.objects.create_user(phone=phone, password=phone)
    user.first_name = instance.agent_name
    user.role = agent_role
    user.agent_profile = instance
    user.save()
