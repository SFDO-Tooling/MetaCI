from github3 import login

from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field
from crispy_forms.layout import Fieldset
from crispy_forms.layout import Layout
from crispy_forms.layout import Submit
from django import forms
from django.conf import settings
from mrbelvedereci.notification.models import RepositoryNotification
from mrbelvedereci.notification.models import BranchNotification
from mrbelvedereci.notification.models import PlanNotification

class AddRepositoryNotificationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AddRepositoryNotificationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-vertical'
        self.helper.form_id = 'add-repository-notification-form'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(
                'Select the repository you want to received notification for',
                Field('repo', css_class='slds-input'),
                Field('user', css_class='slds-input'),
                css_class='slds-form-element',
            ),
            Fieldset(
                'Select the build statuses that should trigger a notification',
                Field('on_success', css_class='slds-input'),
                Field('on_fail', css_class='slds-input'),
                Field('on_error', css_class='slds-input'),
                css_class='slds-form-element',
            ),
            FormActions(
                Submit('submit', 'Submit',
                       css_class='slds-button slds-button--brand')
            ),
        )

    class Meta:
        model = RepositoryNotification
        fields = ['repo','user','on_success','on_fail','on_error']
        widgets = {'user': forms.HiddenInput()}

class AddBranchNotificationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AddBranchNotificationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-vertical'
        self.helper.form_id = 'add-branch-notification-form'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(
                'Select the branch you want to received notification for',
                Field('branch', css_class='slds-input'),
                Field('user', css_class='slds-input'),
                css_class='slds-form-element',
            ),
            Fieldset(
                'Select the build statuses that should trigger a notification',
                Field('on_success', css_class='slds-input'),
                Field('on_fail', css_class='slds-input'),
                Field('on_error', css_class='slds-input'),
                css_class='slds-form-element',
            ),
            FormActions(
                Submit('submit', 'Submit',
                       css_class='slds-button slds-button--brand')
            ),
        )

    class Meta:
        model = BranchNotification
        fields = ['branch','user','on_success','on_fail','on_error']
        widgets = {'user': forms.HiddenInput()}

class AddPlanNotificationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AddPlanNotificationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-vertical'
        self.helper.form_id = 'add-plan-notification-form'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(
                'Select the plan you want to received notification for',
                Field('plan', css_class='slds-input'),
                Field('user', css_class='slds-input'),
                css_class='slds-form-element',
            ),
            Fieldset(
                'Select the build statuses that should trigger a notification',
                Field('on_success', css_class='slds-input'),
                Field('on_fail', css_class='slds-input'),
                Field('on_error', css_class='slds-input'),
                css_class='slds-form-element',
            ),
            FormActions(
                Submit('submit', 'Submit',
                       css_class='slds-button slds-button--brand')
            ),
        )

    class Meta:
        model = PlanNotification
        fields = ['plan','user','on_success','on_fail','on_error']
        widgets = {'user': forms.HiddenInput()}


class DeleteNotificationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(DeleteNotificationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-vertical'
        self.helper.form_id = 'delete-notification-form'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(
                'Are you sure you want to delete this notification?',
                css_class='slds-form-element',
            ),
            FormActions(
                Submit(
                    'action',
                    'Cancel',
                    css_class='slds-button slds-button--neutral',
                ),
                Submit(
                    'action',
                    'Delete',
                    css_class='slds-button slds-button--destructive',
                ),
            ),
        )
