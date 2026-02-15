from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Competition, Tasfiya


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
