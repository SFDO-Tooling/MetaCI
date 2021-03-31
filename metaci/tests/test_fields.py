"""based on django-fernet-fields https://github.com/orcasgit/django-fernet-fields

Copyright (c) 2015 ORCAS, Inc
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above
      copyright notice, this list of conditions and the following
      disclaimer in the documentation and/or other materials provided
      with the distribution.
    * Neither the name of the author nor the names of other
      contributors may be used to endorse or promote products derived
      from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import pytest
from cryptography.fernet import Fernet
from django.core.exceptions import FieldError, ImproperlyConfigured
from django.db import connection
from django.db import models as dj_models

from .. import fields
from . import models


class TestEncryptedField(object):
    def test_key_from_settings(self, settings):
        """If present, use settings.DB_ENCRYPTION_KEYS."""
        f = fields.EncryptedTextField()
        assert f.keys == settings.DB_ENCRYPTION_KEYS

    def test_key_rotation(self, settings):
        """Can supply multiple `keys` for key rotation."""
        settings.DB_ENCRYPTION_KEYS = [Fernet.generate_key(), Fernet.generate_key()]
        f = fields.EncryptedTextField()

        enc1 = Fernet(f.keys[0]).encrypt(b"enc1")
        enc2 = Fernet(f.keys[1]).encrypt(b"enc2")

        assert f.fernet.decrypt(enc1) == b"enc1"
        assert f.fernet.decrypt(enc2) == b"enc2"

    @pytest.mark.parametrize("key", ["primary_key", "db_index", "unique"])
    def test_not_allowed(self, key):
        with pytest.raises(ImproperlyConfigured):
            fields.EncryptedCharField(**{key: True})

    def test_get_char_field_validators(self):
        f = fields.EncryptedCharField()

        # Raises no error
        f.validators


@pytest.mark.parametrize(
    "model,vals",
    [
        (models.EncryptedText, ["foo", "bar"]),
        (models.EncryptedChar, ["one", "two"]),
    ],
)
class TestEncryptedFieldQueries(object):
    def test_insert(self, db, model, vals):
        """Data stored in DB is actually encrypted."""
        field = model._meta.get_field("value")
        model.objects.create(value=vals[0])
        with connection.cursor() as cur:
            cur.execute("SELECT value FROM %s" % model._meta.db_table)
            data = [
                field.fernet.decrypt(r[0].tobytes()).decode("utf-8")
                for r in cur.fetchall()
            ]

        assert list(map(field.to_python, data)) == [vals[0]]

    def test_insert_and_select(self, db, model, vals):
        """Data round-trips through insert and select."""
        model.objects.create(value=vals[0])
        found = model.objects.get()

        assert found.value == vals[0]

    def test_update_and_select(self, db, model, vals):
        """Data round-trips through update and select."""
        model.objects.create(value=vals[0])
        model.objects.update(value=vals[1])
        found = model.objects.get()

        assert found.value == vals[1]

    def test_lookups_raise_field_error(self, db, model, vals):
        """Lookups are not allowed (they cannot succeed)."""
        model.objects.create(value=vals[0])
        field_name = model._meta.get_field("value").__class__.__name__
        lookups = set(dj_models.Field.class_lookups) - set(["isnull"])

        for lookup in lookups:
            with pytest.raises(FieldError) as exc:
                model.objects.get(**{"value__" + lookup: vals[0]})
            assert field_name in str(exc.value)
            assert lookup in str(exc.value)
            assert "does not support lookups" in str(exc.value)


def test_nullable(db):
    """Encrypted/dual/hash field can be nullable."""
    models.EncryptedNullable.objects.create(value=None)
    found = models.EncryptedNullable.objects.get()

    assert found.value is None


def test_isnull_false_lookup(db):
    """isnull False lookup succeeds on nullable fields"""
    test_val = {"test": 1}
    models.EncryptedNullable.objects.create(value=None)
    models.EncryptedNullable.objects.create(value=test_val)
    found = models.EncryptedNullable.objects.get(value__isnull=False)

    assert found.value == test_val


def test_isnull_true_lookup(db):
    """isnull True lookup succeeds on nullable fields"""
    test_val = {"test": 1}
    models.EncryptedNullable.objects.create(value=None)
    models.EncryptedNullable.objects.create(value=test_val)
    found = models.EncryptedNullable.objects.get(value__isnull=True)

    assert found.value is None
