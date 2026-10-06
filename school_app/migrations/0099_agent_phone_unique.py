from django.db import migrations, models


def deduplicate_agent_phones(apps, schema_editor):
    """Append _dup_N to duplicate agent phones so the unique index can be created."""
    Agent = apps.get_model('school_app', 'Agent')
    seen = {}
    for agent in Agent.objects.order_by('id'):
        phone = agent.phone or ''
        if phone in seen:
            seen[phone] += 1
            agent.phone = f"{phone}_dup_{seen[phone]}"
            agent.save(update_fields=['phone'])
        else:
            seen[phone] = 0


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0098_dailyabsence_agent_response'),
    ]

    operations = [
        migrations.RunPython(deduplicate_agent_phones, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='agent',
            name='phone',
            field=models.CharField(max_length=20, unique=True),
        ),
    ]
