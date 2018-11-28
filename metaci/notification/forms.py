from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field
from crispy_forms.layout import Fieldset
from crispy_forms.layout import Layout
from crispy_forms.layout import Submit
from django import forms


class AddNotificationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AddNotificationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "form-vertical"
        self.helper.form_id = "add-repository-notification-form"
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Fieldset(
                "Select the target you want to receive notifications for",
                Field("target", css_class="slds-input"),
                css_class="slds-form-element",
            ),
            Fieldset(
                "Select the build statuses that should trigger a notification",
                Field("on_success", css_class="slds-input"),
                Field("on_fail", css_class="slds-input"),
                Field("on_error", css_class="slds-input"),
                css_class="slds-form-element",
            ),
            FormActions(
                Submit("submit", "Submit", css_class="slds-button slds-button--brand")
            ),
        )

    class Meta:
        fields = ["target", "on_success", "on_error", "on_fail"]
