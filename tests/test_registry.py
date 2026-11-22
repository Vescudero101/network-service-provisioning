"""Every service and feature must have its required parts. This also catches 'forgot to register it'."""
from pathlib import Path

from nsp.features.registry import FEATURE_ORDER, FEATURES
from nsp.services.registry import SERVICES

REQUIRED_FEATURE_FUNCTIONS = ["fill_actions", "split_by_action", "commands_to_collect",
                              "parse_output", "validate", "check_result"]


def test_every_service_has_the_required_parts():
    for name, service in SERVICES.items():
        assert service.TITLE, name
        assert set(service.ACTIONS) == {"deploy", "cease"}, name
        for action_name, action in service.ACTIONS.items():
            where = f"{name}/{action_name}"
            assert action["label"] and action["description"], where
            assert callable(action["create_service_intent"]), where
            field_names = [field["name"] for field in action["fields"]]
            assert "reference" in field_names, where
            for field in action["fields"]:
                assert field["label"] and field["kind"] in ("text", "int", "select"), where


def test_every_feature_has_the_required_functions():
    for name, feature in FEATURES.items():
        assert isinstance(feature.IMPLEMENTED, bool), name
        for function_name in REQUIRED_FEATURE_FUNCTIONS:
            assert callable(getattr(feature, function_name)), f"{name}.{function_name}"


def test_feature_order_lists_every_feature_once():
    assert sorted(FEATURE_ORDER) == sorted(FEATURES)


def test_every_feature_has_a_template_for_the_default_platform():
    templates = Path(__file__).parents[1] / "src" / "nsp" / "templates" / "cisco_iosxe"
    for name in FEATURES:
        assert (templates / f"{name}.j2").exists(), name
