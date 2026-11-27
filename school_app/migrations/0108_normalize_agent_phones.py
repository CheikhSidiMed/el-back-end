"""Remove the Mauritanian country code from stored agent phone numbers.

'0022221212123' / '+22221212123' / '22221212123'  →  '21212123'

Only numbers that are exactly 222 + 8 digits are changed; foreign numbers and
malformed values are left as they are. Agent.phone is unique: when the stripped
number already belongs to another agent (same person entered twice), that agent's
`phone` is NOT changed and is printed so it can be merged by hand.
"""
import re

from django.db import migrations

MR_PREFIXED = re.compile(r'^(?:\+|00)?222(\d{8})$')


def _strip(value):
    if not value:
        return value
    m = MR_PREFIXED.match(re.sub(r'[\s\-]', '', str(value)))
    return m.group(1) if m else value


def normalize_agent_phones(apps, schema_editor):
    Agent = apps.get_model('school_app', 'Agent')
    taken = set(Agent.objects.values_list('phone', flat=True))
    changed, skipped = 0, []

    for agent in Agent.objects.all().order_by('id'):
        fields = []

        new_phone = _strip(agent.phone)
        if new_phone != agent.phone:
            if new_phone in taken:
                skipped.append((agent.id, agent.phone, new_phone))
            else:
                taken.discard(agent.phone)
                taken.add(new_phone)
                agent.phone = new_phone
                fields.append('phone')

        for field in ('phone_2', 'whatsapp_phone'):
            old = getattr(agent, field)
            new = _strip(old)
            if new != old:
                setattr(agent, field, new)
                fields.append(field)

        if fields:
            # update_fields + historical model: no custom save()/signals run here
            agent.save(update_fields=fields)
            changed += 1

    print(f'\n  normalize_agent_phones: {changed} agents updated')
    for agent_id, old, new in skipped:
        print(f'  ! agent {agent_id}: phone {old} kept — {new} already used by another agent (merge by hand)')


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0107_evaluation_month_result_text_fields'),
    ]

    operations = [
        migrations.RunPython(normalize_agent_phones, migrations.RunPython.noop),
    ]
