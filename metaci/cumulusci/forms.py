from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from django import forms


class OrgLockForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(OrgLockForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "form-vertical"
        self.helper.form_id = "org-lock-form"
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            FormActions(
                Submit(
                    "action", "Cancel", css_class="slds-button slds-button--neutral"
                ),
                Submit(
                    "action", "Lock", css_class="slds-button slds-button--destructive"
                ),
            )
        )


class OrgUnlockForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(OrgUnlockForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "form-vertical"
        self.helper.form_id = "org-unlock-form"
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            FormActions(
                Submit(
                    "action", "Cancel", css_class="slds-button slds-button--neutral"
                ),
                Submit(
                    "action", "Unlock", css_class="slds-button slds-button--destructive"
                ),
            )
        )
