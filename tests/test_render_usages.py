"""Tests for usages and "Extended by" rendering.

Uses tests/samples/inherited_elements_demo.xsd which has extension chains:
- AnimalBase → Dog → ServiceDog (extension chain)
- VehicleBase → Car → ElectricCar (extension chain)
- LocationBase → PreciseLocation (restriction) → GeoFence → MonitoredGeoFence

All types/elements are prefixed with "tns:" due to the schema's targetNamespace.
"""

import re

import pytest
from conftest import SAMPLES_DIR, get_template

INHERITED_XSD = SAMPLES_DIR / "inherited_elements_demo.xsd"
NS = "tns:"


def _get_usage_links(html: str, data_type: str, path: str) -> list[str]:
    """Extract the link texts (type/element names) listed in a *-usages template."""
    content = get_template(html, data_type, path)
    return [m.strip() for m in re.findall(r"<a[^>]*>([\s\S]*?)</a>", content)]


@pytest.fixture(scope="module")
def rendered_html():
    from xsd_browser.main import render_html

    return render_html(INHERITED_XSD, minify=False)


class TestExtendedBy:
    """Types that are extended should show an "Extended by" box listing derived types."""

    def test_extended_by_section(self, rendered_html):
        # AnimalBase is extended by Dog → should have an extended-by-box
        content = get_template(
            rendered_html,
            "type-contents",
            NS + "AnimalBase",
        )
        assert 'class="extended-by-box"' in content

    def test_extended_by_lists_derived_types(self, rendered_html):
        content = get_template(
            rendered_html,
            "type-contents",
            NS + "AnimalBase",
        )
        assert NS + "Dog" in content

    def test_extended_by_absent_for_leaf(self, rendered_html):
        # ServiceDog has no derived types → no extended-by-box
        content = get_template(
            rendered_html,
            "type-contents",
            NS + "ServiceDog",
        )
        assert "extended-by-box" not in content


class TestTypeUsages:
    """Verify exact "Used by" lists for types — only direct users, no indirect ancestors."""

    def test_animal_base_usages(self, rendered_html):
        """AnimalBase → Dog → ServiceDog: only Dog (direct) and Animal element."""
        usages = set(_get_usage_links(rendered_html, "type-usages", NS + "AnimalBase"))
        assert usages == {NS + "Dog", NS + "Animal"}

    def test_dog_usages(self, rendered_html):
        """Dog is used by ServiceDog (extends) and Dog element (type attr)."""
        usages = set(_get_usage_links(rendered_html, "type-usages", NS + "Dog"))
        assert usages == {NS + "ServiceDog", NS + "Dog"}

    def test_service_dog_usages(self, rendered_html):
        """ServiceDog is a leaf type, only used by its element."""
        usages = set(_get_usage_links(rendered_html, "type-usages", NS + "ServiceDog"))
        assert usages == {NS + "ServiceDog"}

    def test_vehicle_base_usages(self, rendered_html):
        """VehicleBase → Car → ElectricCar: only Car (direct) and Vehicle element."""
        usages = set(_get_usage_links(rendered_html, "type-usages", NS + "VehicleBase"))
        assert usages == {NS + "Car", NS + "Vehicle"}

    def test_car_usages(self, rendered_html):
        usages = set(_get_usage_links(rendered_html, "type-usages", NS + "Car"))
        assert usages == {NS + "ElectricCar", NS + "Car"}

    def test_electric_car_usages(self, rendered_html):
        usages = set(_get_usage_links(rendered_html, "type-usages", NS + "ElectricCar"))
        assert usages == {NS + "ElectricCar"}

    def test_location_base_usages(self, rendered_html):
        """LocationBase → PreciseLocation → GeoFence → MonitoredGeoFence."""
        usages = set(_get_usage_links(rendered_html, "type-usages", NS + "LocationBase"))
        assert usages == {NS + "PreciseLocation", NS + "Location"}

    def test_precise_location_usages(self, rendered_html):
        usages = set(_get_usage_links(rendered_html, "type-usages", NS + "PreciseLocation"))
        assert usages == {NS + "GeoFence", NS + "PreciseLocation"}

    def test_geo_fence_usages(self, rendered_html):
        usages = set(_get_usage_links(rendered_html, "type-usages", NS + "GeoFence"))
        assert usages == {NS + "MonitoredGeoFence", NS + "GeoFence"}

    def test_monitored_geo_fence_usages(self, rendered_html):
        usages = set(_get_usage_links(rendered_html, "type-usages", NS + "MonitoredGeoFence"))
        assert usages == {NS + "MonitoredGeoFence"}

    def test_sensor_base_usages(self, rendered_html):
        """SensorBase → TemperatureSensor → CalibratedTempSensor → HighAccuracySensor."""
        usages = set(_get_usage_links(rendered_html, "type-usages", NS + "SensorBase"))
        assert usages == {NS + "TemperatureSensor", NS + "Sensor"}

    def test_temperature_sensor_usages(self, rendered_html):
        usages = set(_get_usage_links(rendered_html, "type-usages", NS + "TemperatureSensor"))
        assert usages == {NS + "CalibratedTempSensor", NS + "TemperatureSensor"}

    def test_calibrated_temp_sensor_usages(self, rendered_html):
        usages = set(
            _get_usage_links(rendered_html, "type-usages", NS + "CalibratedTempSensor")
        )
        assert usages == {NS + "HighAccuracySensor", NS + "CalibratedTempSensor"}

    def test_high_accuracy_sensor_usages(self, rendered_html):
        usages = set(_get_usage_links(rendered_html, "type-usages", NS + "HighAccuracySensor"))
        assert usages == {NS + "HighAccuracySensor"}
