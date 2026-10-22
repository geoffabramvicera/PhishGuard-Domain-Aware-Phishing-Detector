"""Offline unit tests for domain-aware and URL-structure analysis."""
import unittest

from url_features import (
    explain_domain,
    explain_url_structure,
    extract_features,
    get_group_domain,
    get_url_parts,
    known_major_domain,
    recognized_major_homepage,
    split_domain,
    validate_url,
)


class DomainAwareFeatureTests(unittest.TestCase):
    def test_domain_split_with_common_multi_label_suffix(self):
        reg, suffix, subdomains = split_domain("login.accounts.example.co.uk")
        self.assertEqual(reg, "example.co.uk")
        self.assertEqual(suffix, "co.uk")
        self.assertEqual(subdomains, 2)

    def test_domain_split_with_github_pages_private_suffix(self):
        reg, suffix, subdomains = split_domain("project.github.io")
        self.assertEqual(reg, "project.github.io")
        self.assertEqual(suffix, "github.io")
        self.assertEqual(subdomains, 0)

    def test_feature_sets_separate_host_and_url_signals(self):
        features = extract_features("https://secure-example.com/login/verify?return=123")
        self.assertGreater(features["hostname_length"], 0)
        self.assertGreater(features["path_depth"], 0)
        self.assertGreater(features["suspicious_path_term_count"], 0)
        self.assertIn("brand_token_in_subdomain", features)
        self.assertIn("hostname_entropy", features)

    def test_known_homepage_rule_is_narrow(self):
        self.assertEqual(recognized_major_homepage("https://github.com"), "github.com")
        self.assertIsNone(recognized_major_homepage("https://github.com/login"))
        self.assertIsNone(recognized_major_homepage("https://github.com.evil.example"))
        self.assertIsNone(recognized_major_homepage("https://github.com/?redirect=evil"))
        self.assertIsNone(recognized_major_homepage("http://github.com"))

    def test_looks_like_brand_in_subdomain(self):
        features = extract_features("https://paypal.login.evil.example/verify")
        self.assertEqual(features["brand_token_in_subdomain"], 1)

    def test_validation_rejects_bad_inputs(self):
        self.assertIsNotNone(validate_url(""))
        self.assertIsNotNone(validate_url("javascript:alert(1)"))
        self.assertIsNone(validate_url("https://example.com"))

    def test_domain_grouping_uses_registrable_domain(self):
        self.assertEqual(get_group_domain("https://login.example.co.uk/page"), "example.co.uk")

    def test_parts_show_domain_not_path_as_hostname(self):
        parts = get_url_parts("https://github.com/orgs/openai").copy()
        self.assertEqual(parts["hostname_ascii"], "github.com")
        self.assertEqual(parts["registered_domain"], "github.com")
        self.assertEqual(parts["path"], "/orgs/openai")

    def test_analysis_has_separate_domain_and_url_findings(self):
        self.assertIn("indicators", explain_domain("https://verify-paypal.evil.example"))
        self.assertIn("indicators", explain_url_structure("https://example.com/login?verify=yes"))


if __name__ == "__main__":
    unittest.main()
