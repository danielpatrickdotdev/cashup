# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-07 15:05
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cashup', '0011_auto_20170105_2122'),
    ]

    operations = [
        migrations.RenameField(
            model_name='till',
            old_name='name',
            new_name='outlet_name',
        ),
        migrations.RemoveField(
            model_name='till',
            name='location',
        ),
    ]