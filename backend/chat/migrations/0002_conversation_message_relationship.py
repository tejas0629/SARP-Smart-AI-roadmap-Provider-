from django.db import migrations, models
import django.db.models.deletion


def assign_existing_messages(apps, schema_editor):
    Conversation = apps.get_model('chat', 'Conversation')
    ChatMessage = apps.get_model('chat', 'ChatMessage')
    conversation = Conversation.objects.create()
    ChatMessage.objects.filter(conversation__isnull=True).update(conversation=conversation)


class Migration(migrations.Migration):
    dependencies = [
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='conversation',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='messages',
                to='chat.conversation',
            ),
        ),
        migrations.RunPython(assign_existing_messages, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='chatmessage',
            name='conversation',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='messages',
                to='chat.conversation',
            ),
        ),
    ]
