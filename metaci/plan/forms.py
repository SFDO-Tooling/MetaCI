from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field
from crispy_forms.layout import Fieldset
from crispy_forms.layout import Layout
from crispy_forms.layout import Submit
from django import forms
from django.conf import settings
from metaci.repository.models import Branch
from metaci.build.models import Build


class RunPlanForm(forms.Form):
    branch = forms.ChoiceField(choices=(), label="Branch")
    commit = forms.CharField(required=False)
    keep_org = forms.BooleanField(required=False)
    release = forms.ModelChoiceField(None, required=False)
    org_note = forms.CharField(required=False)

    def __init__(self, planrepo, user, *args, **kwargs):
        self.planrepo = planrepo
        self.plan = planrepo.plan
        self.repo = planrepo.repo
        self.user = user
        org = kwargs.pop("org", None)
        self.org = org
        super(RunPlanForm, self).__init__(*args, **kwargs)
        self.fields["branch"].choices = self._get_branch_choices()
        self.fields["release"].queryset = self.repo.releases
        self.helper = FormHelper()
        self.helper.form_class = "form-vertical"
        self.helper.form_id = "run-build-form"
        self.helper.form_method = "post"
        self.advanced_mode = False
        if "advanced_mode" in args[0]:
            self.advanced_mode = args[0]["advanced_mode"] == "1"
        self.helper.layout = Layout(
            Fieldset(
                "Choose the branch you want to build",
                Field("branch", css_class="slds-input"),
                css_class="slds-form-element",
            ),
            Fieldset(
                "A custom note about the org being created",
                Field("org_note", css_class="slds-input"),
                css_class="slds-form-element",
            ),
        )
        if self.advanced_mode:
            self.helper.layout.extend(
                [
                    Fieldset(
                        "Keep org? (scratch orgs only)",
                        Field("keep_org", css_class="slds-checkbox"),
                        css_class="slds-form-element",
                    ),
                    Fieldset(
                        "Enter the commit you want to build.  The HEAD commit on the branch will be used if you do not specify a commit",
                        Field("commit", css_class="slds-input"),
                        css_class="slds-form-element",
                    ),
                    Fieldset(
                        "What release is this connected to?",
                        Field("release", css_class="slds-input"),
                        css_class="slds-form-element",
                    ),
                ]
            )
        else:
            self.helper.layout.extend([Field("keep_org")])
        self.helper.layout.append(
            FormActions(
                Submit(
                    "submit",
                    "Submit",
                    css_class="slds-button slds-button--brand slds-m-around--medium",
                )
            )
        )

    def _get_branch_choices(self):
        gh_repo = self.repo.github_api
        choices = [(gh_repo.default_branch, gh_repo.default_branch)]
        for branch in gh_repo.branches():
            if branch.name != gh_repo.default_branch:
                choices.append((branch.name, branch.name))
        return tuple(choices)

    def create_build(self):

        commit = self.cleaned_data.get("commit")
        if not commit:
            gh_repo = self.repo.github_api
            gh_branch = gh_repo.branch(self.cleaned_data["branch"])
            commit = gh_branch.commit.sha

        release = self.cleaned_data.get("release")

        branch, created = Branch.objects.get_or_create(
            repo=self.repo, name=self.cleaned_data["branch"]
        )
        if branch.is_removed:
            # resurrect the soft deleted branch
            branch.is_removed = False
            branch.save()

        keep_org = self.cleaned_data.get("keep_org")
        org_note = self.cleaned_data.get("org_note")

        build = Build(
            repo=self.repo,
            plan=self.plan,
            planrepo=self.planrepo,
            org=self.org,
            branch=branch,
            commit=commit,
            keep_org=keep_org,
            build_type="manual",
            user=self.user,
            release=release,
            org_note=org_note,
            release_relationship_type="manual",
        )

        build.save()

        return build
