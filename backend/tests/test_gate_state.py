import unittest

from app.gate_state import PendingGate, profile_config_hash, resolve_pending_gate
from app.profiles import GateProfile, GateStage, GateTemplate


def make_profile(*, template_id: str = "cookie-consent", threshold: int = 1) -> GateProfile:
    return GateProfile(
        profile_id="click-cookie",
        gates=(
            GateStage(
                gate_type="click",
                templates=(
                    GateTemplate(
                        template_id=template_id,
                        parameters={"required_clicks": threshold},
                    ),
                ),
            ),
        ),
    )


class ProfileConfigHashTests(unittest.TestCase):
    def test_same_profile_has_same_hash(self) -> None:
        self.assertEqual(profile_config_hash(make_profile()), profile_config_hash(make_profile()))

    def test_stage_configuration_changes_hash(self) -> None:
        original_hash = profile_config_hash(make_profile())
        self.assertNotEqual(original_hash, profile_config_hash(make_profile(template_id="alert")))
        self.assertNotEqual(original_hash, profile_config_hash(make_profile(threshold=2)))


class ResolvePendingGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pending = PendingGate(
            session_id="session-a",
            target_path="/kit2/?x=1",
            kit_root="kit2",
            dataset="phishdecloaker",
            profile_id="click-cookie",
            config_hash="config-a",
            stage_index=0,
            gate_type="click",
            template_id="cookie-consent",
            parameters={},
            display_context={"variant_id": "compact.standard.slate"},
            research_session_id="research-a",
            log_target_path="/opaque/",
            issued_monotonic=1.0,
        )
        self.pending_gates = {"token-a": self.pending}

    def resolve(self, session_id: str | None = "session-a", **overrides: str):
        return resolve_pending_gate(
            self.pending_gates,
            "token-a",
            session_id,
            active_profile_id=overrides.get("profile_id", "click-cookie"),
            active_config_hash=overrides.get("config_hash", "config-a"),
        )

    def test_matching_session_and_config_resolve_stored_state(self) -> None:
        resolved = self.resolve()
        self.assertIs(resolved, self.pending)
        self.assertEqual(
            resolved.display_context["variant_id"],
            "compact.standard.slate",
        )

    def test_other_session_cannot_reuse_token(self) -> None:
        self.assertIsNone(self.resolve("session-b"))

    def test_changed_profile_or_config_invalidates_token(self) -> None:
        self.assertIsNone(self.resolve(profile_id="click-alert"))
        self.assertIsNone(self.resolve(config_hash="config-b"))

    def test_non_initial_stage_is_not_accepted_by_single_stage_runtime(self) -> None:
        later_stage = PendingGate(
            session_id="session-a",
            target_path="/kit2/",
            kit_root="kit2",
            dataset="phishdecloaker",
            profile_id="click-cookie",
            config_hash="config-a",
            stage_index=1,
            gate_type="click",
            template_id="cookie-consent",
            parameters={},
            display_context={},
            research_session_id="research-a",
            log_target_path="/opaque/",
            issued_monotonic=1.0,
        )
        self.assertIsNone(
            resolve_pending_gate(
                {"token-a": later_stage},
                "token-a",
                "session-a",
                active_profile_id="click-cookie",
                active_config_hash="config-a",
            )
        )


if __name__ == "__main__":
    unittest.main()
