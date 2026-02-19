"""Tests for usages and "Extended by" rendering.

Uses tests/samples/inherited_elements_demo.xsd which has extension chains:
- AnimalBase → Dog → ServiceDog (extension chain)
- VehicleBase → Car → ElectricCar (extension chain)
- LocationBase → PreciseLocation (restriction) → GeoFence → MonitoredGeoFence

All types/elements are prefixed with "tns:" due to the schema's targetNamespace.
"""

import pytest
from conftest import SAMPLES_DIR, get_template, inner_html, parse_html

INHERITED_XSD = SAMPLES_DIR / "inherited_elements_demo.xsd"
NS = "tns:"


def _get_usage_links(doc, data_type: str, path: str) -> list[str]:
    """Extract the link texts (type/element names) listed in a *-usages template."""
    tmpl = get_template(doc, data_type, path)
    return [a.text_content().strip() for a in tmpl.xpath('.//a')]


@pytest.fixture(scope="module")
def doc():
    from xsd_browser.main import render_html

    html = render_html(INHERITED_XSD, minify=False)
    return parse_html(html)


class TestExtendedBy:
    """Types that are extended should show an "Extended by" box listing derived types."""

    def test_extended_by_section(self, doc):
        # AnimalBase is extended by Dog → should have an extended-by-box
        tmpl = get_template(doc, "type-contents", NS + "AnimalBase")
        assert tmpl.xpath('.//*[@class="extended-by-box"]')

    def test_extended_by_lists_derived_types(self, doc):
        tmpl = get_template(doc, "type-contents", NS + "AnimalBase")
        content = inner_html(tmpl)
        assert NS + "Dog" in content

    def test_extended_by_absent_for_leaf(self, doc):
        # ServiceDog has no derived types → no extended-by-box
        tmpl = get_template(doc, "type-contents", NS + "ServiceDog")
        assert not tmpl.xpath('.//*[@class="extended-by-box"]')


class TestTypeUsages:
    """Verify exact "Used by" lists for types — only direct users, no indirect ancestors."""

    def test_animal_base_usages(self, doc):
        """AnimalBase → Dog → ServiceDog: only Dog (direct) and Animal element."""
        usages = set(_get_usage_links(doc, "type-usages", NS + "AnimalBase"))
        assert usages == {NS + "Dog", NS + "Animal"}

    def test_dog_usages(self, doc):
        """Dog is used by ServiceDog (extends) and Dog element (type attr)."""
        usages = set(_get_usage_links(doc, "type-usages", NS + "Dog"))
        assert usages == {NS + "ServiceDog", NS + "Dog"}

    def test_service_dog_usages(self, doc):
        """ServiceDog is a leaf type, only used by its element."""
        usages = set(_get_usage_links(doc, "type-usages", NS + "ServiceDog"))
        assert usages == {NS + "ServiceDog"}

    def test_vehicle_base_usages(self, doc):
        """VehicleBase → Car → ElectricCar: only Car (direct) and Vehicle element."""
        usages = set(_get_usage_links(doc, "type-usages", NS + "VehicleBase"))
        assert usages == {NS + "Car", NS + "Vehicle"}

    def test_car_usages(self, doc):
        usages = set(_get_usage_links(doc, "type-usages", NS + "Car"))
        assert usages == {NS + "ElectricCar", NS + "Car"}

    def test_electric_car_usages(self, doc):
        usages = set(_get_usage_links(doc, "type-usages", NS + "ElectricCar"))
        assert usages == {NS + "ElectricCar"}

    def test_location_base_usages(self, doc):
        """LocationBase → PreciseLocation → GeoFence → MonitoredGeoFence."""
        usages = set(_get_usage_links(doc, "type-usages", NS + "LocationBase"))
        assert usages == {NS + "PreciseLocation", NS + "Location"}

    def test_precise_location_usages(self, doc):
        usages = set(_get_usage_links(doc, "type-usages", NS + "PreciseLocation"))
        assert usages == {NS + "GeoFence", NS + "PreciseLocation"}

    def test_geo_fence_usages(self, doc):
        usages = set(_get_usage_links(doc, "type-usages", NS + "GeoFence"))
        assert usages == {NS + "MonitoredGeoFence", NS + "GeoFence"}

    def test_monitored_geo_fence_usages(self, doc):
        usages = set(_get_usage_links(doc, "type-usages", NS + "MonitoredGeoFence"))
        assert usages == {NS + "MonitoredGeoFence"}

    def test_sensor_base_usages(self, doc):
        """SensorBase → TemperatureSensor → CalibratedTempSensor → HighAccuracySensor."""
        usages = set(_get_usage_links(doc, "type-usages", NS + "SensorBase"))
        assert usages == {NS + "TemperatureSensor", NS + "Sensor"}

    def test_temperature_sensor_usages(self, doc):
        usages = set(_get_usage_links(doc, "type-usages", NS + "TemperatureSensor"))
        assert usages == {NS + "CalibratedTempSensor", NS + "TemperatureSensor"}

    def test_calibrated_temp_sensor_usages(self, doc):
        usages = set(
            _get_usage_links(doc, "type-usages", NS + "CalibratedTempSensor")
        )
        assert usages == {NS + "HighAccuracySensor", NS + "CalibratedTempSensor"}

    def test_high_accuracy_sensor_usages(self, doc):
        usages = set(_get_usage_links(doc, "type-usages", NS + "HighAccuracySensor"))
        assert usages == {NS + "HighAccuracySensor"}
