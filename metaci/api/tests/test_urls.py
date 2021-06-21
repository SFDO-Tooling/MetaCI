import unittest

from rest_framework.reverse import reverse


class TestURLReversals(unittest.TestCase):
    """Test URL patterns for APIs app."""

    def test_list_reverse(self):
        """<entity>-list should reverse to /api/<entity>/."""
        self.assertEqual(reverse("branch-list"), "/api/branches/")
        self.assertEqual(reverse("build-list"), "/api/builds/")
        self.assertEqual(reverse("build_flow-list"), "/api/build_flows/")
        self.assertEqual(reverse("org-list"), "/api/orgs/")
        self.assertEqual(reverse("plan-list"), "/api/plans/")
        self.assertEqual(reverse("plan_repo-list"), "/api/plan_repos/")
        self.assertEqual(reverse("rebuild-list"), "/api/rebuilds/")
        self.assertEqual(reverse("repo-list"), "/api/repos/")
        self.assertEqual(reverse("scratch_org-list"), "/api/scratch_orgs/")
        self.assertEqual(reverse("service-list"), "/api/services/")

    def test_detail_reverse(self):
        """<entity>-detail [1] should reverse to /api/<entity>/1."""
        self.assertEqual(reverse("branch-detail", [1]), "/api/branches/1/")
        self.assertEqual(reverse("build-detail", [1]), "/api/builds/1/")
        self.assertEqual(reverse("build_flow-detail", [1]), "/api/build_flows/1/")
        self.assertEqual(reverse("org-detail", [1]), "/api/orgs/1/")
        self.assertEqual(reverse("plan-detail", [1]), "/api/plans/1/")
        self.assertEqual(reverse("plan_repo-detail", [1]), "/api/plan_repos/1/")
        self.assertEqual(reverse("rebuild-detail", [1]), "/api/rebuilds/1/")
        self.assertEqual(reverse("repo-detail", [1]), "/api/repos/1/")
        self.assertEqual(reverse("scratch_org-detail", [1]), "/api/scratch_orgs/1/")
        self.assertEqual(reverse("service-detail", [1]), "/api/services/1/")
