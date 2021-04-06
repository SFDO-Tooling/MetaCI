from django.db import models

from .. import fields


class EncryptedText(models.Model):
    value = fields.EncryptedTextField()


class EncryptedChar(models.Model):
    value = fields.EncryptedCharField(max_length=25)


class EncryptedNullable(models.Model):
    value = fields.EncryptedJSONField(null=True)
