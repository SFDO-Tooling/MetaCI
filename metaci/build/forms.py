from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field
from crispy_forms.layout import Layout
from crispy_forms.layout import Submit
from django import forms
from django.conf import settings
from django.utils import timezone
from metaci.build.tasks import set_github_status


QA_CHOICES = (
    ("success", "Pass"),
    ("fail", "Fail"),
)


class QATestingForm(forms.Form):
    result = forms.ChoiceField(
        choices=QA_CHOICES,
        label="QA Result",
        widget=forms.RadioSelect(),
    )
    comment = forms.CharField(widget=forms.Textarea())
    delete_org = forms.BooleanField(initial=True)

    def __init__(self, build, user, *args, **kwargs):
        self.build = build
        self.user = user
        super(QATestingForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "form-vertical"
        self.helper.form_id = "qa-testing-form"
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Field("result", css_class="slds-radio"),
            Field("comment", css_class="slds-textarea"),
            Field("delete_org", css_class="slds-checkbox"),
        )
        self.helper.layout.append(
            FormActions(
                Submit("submit", "Submit", css_class="slds-button slds-button--brand")
            )
        )

    def save(self):
        result = self.cleaned_data.get("result")
        comment = self.cleaned_data.get("comment")
        delete_org = self.cleaned_data.get("delete_org")
        if self.build.current_rebuild:
            build = self.build.current_rebuild
        else:
            build = self.build
        build.status = result
        build.qa_comment = comment
        build.qa_user = self.user
        build.time_qa_end = timezone.now()
        build.save()
        if delete_org:
            build.org_instance.delete_org()
        if settings.GITHUB_STATUS_UPDATES_ENABLED:
            set_github_status.delay(self.build.id)
        return build
