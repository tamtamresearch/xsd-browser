"""Tests for inherited element rendering across different complexType patterns.

Uses samples/inherited_elements_demo.xsd which covers:
  Case 1: Direct children (always worked)
  Case 2: complexContent/extension (issue #6)
  Case 3: complexContent/restriction
  Case 4: Multi-level chain mixing all three patterns
  Case 5: simpleContent/extension (attribute-only)
"""

import re
from pathlib import Path

import pytest

SAMPLES_DIR = Path(__file__).resolve().parent / "samples"
XSD_FILE = SAMPLES_DIR / "inherited_elements_demo.xsd"

# The demo schema declares targetNamespace with prefix "tns", so all type names
# in the rendered HTML are prefixed with "tns:" (e.g. "tns:Dog").
NS = "tns:"


@pytest.fixture(scope="module")
def rendered_html():
    """Generate HTML from the demo XSD and return it as a string."""
    from xsd_browser.main import render_html

    return render_html(XSD_FILE, minify=False)


def _get_type_template(html: str, data_type: str, type_name: str) -> str:
    """Extract the content of a <template data-type="..." ... data-path="..."> block.

    Template tags span multiple lines and have other attributes between data-type
    and data-path (data-name, data-substgroup). We use [^>]* to stay within the
    opening tag (in Python regex, [^>] matches newlines too, unlike '.').
    """
    pattern = (
        rf'<template\s+data-type="{re.escape(data_type)}"'
        rf'[^>]*data-path="{re.escape(type_name)}"[^>]*>([\s\S]*?)</template>'
    )
    m = re.search(pattern, html)
    assert m, f"Template not found: data-type={data_type!r} data-path={type_name!r}"
    return m.group(1)


def _get_inherited_section(html: str, type_name: str) -> str:
    """Extract all 'Inherited from ...' section(s) for a given type."""
    content = _get_type_template(html, "type-contents", type_name)
    # Inherited sections: <div class="inherited-section">...</div> (with nested divs)
    parts = re.findall(
        r'<div class="inherited-section">[\s\S]*?</div>\s*</div>\s*</div>',
        content,
    )
    return "\n".join(parts)


def _extract_element_names_from_section(section_html: str) -> list[str]:
    """Extract element names from xbe-collapsible-element-ref tags."""
    # The attribute is element="name", not name="name"
    return re.findall(r'<xbe-collapsible-element-ref\s+element="([^"]+)"', section_html)


def _get_all_inherited_element_names(html: str, type_name: str) -> list[str]:
    """Get all element names shown in inherited sections for a type."""
    inherited = _get_inherited_section(html, type_name)
    return _extract_element_names_from_section(inherited)


def _get_inherited_from(html: str, type_name: str, base_name: str) -> list[str]:
    """Get element names inherited from a specific base type."""
    content = _get_type_template(html, "type-contents", type_name)
    # The inherited section references the base type via a link like:
    #   <a class="type-link" href="#type-tns:BaseName">tns:BaseName</a>
    pattern = (
        rf'<div class="inherited-section">\s*'
        rf'<div class=note>Inherited from[\s\S]*?'
        rf'#type-{re.escape(base_name)}[\s\S]*?'
        rf'<div class="extension-content inherited">([\s\S]*?)</div>\s*</div>'
    )
    m = re.search(pattern, content)
    if not m:
        return []
    return _extract_element_names_from_section(m.group(1))


def _get_own_element_names(html: str, type_name: str) -> list[str]:
    """Get element names defined directly by the type (in 'New elements' or top-level)."""
    content = _get_type_template(html, "type-contents", type_name)
    # Remove inherited sections to isolate own elements
    without_inherited = re.sub(
        r'<div class="inherited-section">[\s\S]*?</div>\s*</div>\s*</div>',
        "",
        content,
    )
    return _extract_element_names_from_section(without_inherited)


# ===================================================================
# Case 1: Direct children (always worked)
# ===================================================================


class TestCase1DirectChildren:
    """AnimalBase (direct) -> Dog (extension) -> ServiceDog (extension)."""

    def test_dog_inherits_from_animal_base(self, rendered_html):
        inherited = _get_all_inherited_element_names(rendered_html, NS + "Dog")
        assert "name" in inherited
        assert "species" in inherited

    def test_dog_own_elements(self, rendered_html):
        own = _get_own_element_names(rendered_html, NS + "Dog")
        assert "breed" in own

    def test_service_dog_inherits_breed_from_dog(self, rendered_html):
        """This is the key test: breed lives inside Dog's extension node."""
        inherited = _get_inherited_from(rendered_html, NS + "ServiceDog", NS + "Dog")
        assert "breed" in inherited

    def test_service_dog_inherits_from_animal_base_transitively(self, rendered_html):
        """Transitive: ServiceDog -> Dog -> AnimalBase. Dog's template shows AnimalBase's elements."""
        inherited = _get_all_inherited_element_names(rendered_html, NS + "Dog")
        assert "name" in inherited
        assert "species" in inherited

    def test_service_dog_own_elements(self, rendered_html):
        own = _get_own_element_names(rendered_html, NS + "ServiceDog")
        assert "certificationId" in own
        assert "handler" in own


# ===================================================================
# Case 2: complexContent/extension (issue #6)
# ===================================================================


class TestCase2ComplexContentExtension:
    """VehicleBase (direct) -> Car (extension) -> ElectricCar (extension)."""

    def test_car_inherits_from_vehicle_base(self, rendered_html):
        inherited = _get_inherited_from(rendered_html, NS + "Car", NS + "VehicleBase")
        assert "vin" in inherited
        assert "manufacturer" in inherited
        assert "yearOfManufacture" in inherited

    def test_car_own_elements(self, rendered_html):
        own = _get_own_element_names(rendered_html, NS + "Car")
        assert "numberOfDoors" in own
        assert "trunkCapacityLitre" in own

    def test_electric_car_inherits_from_car(self, rendered_html):
        """Core issue #6 test: Car's elements are inside complexContent/extension."""
        inherited = _get_inherited_from(rendered_html, NS + "ElectricCar", NS + "Car")
        assert "numberOfDoors" in inherited
        assert "trunkCapacityLitre" in inherited

    def test_electric_car_inherits_from_vehicle_base_transitively(self, rendered_html):
        """Transitive: ElectricCar -> Car -> VehicleBase. Car's template shows VehicleBase's elements."""
        inherited = _get_inherited_from(rendered_html, NS + "Car", NS + "VehicleBase")
        assert "vin" in inherited
        assert "manufacturer" in inherited
        assert "yearOfManufacture" in inherited

    def test_electric_car_own_elements(self, rendered_html):
        own = _get_own_element_names(rendered_html, NS + "ElectricCar")
        assert "batteryCapacityKWh" in own
        assert "rangeKm" in own
        assert "chargingStandard" in own


# ===================================================================
# Case 3: complexContent/restriction
# ===================================================================


class TestCase3ComplexContentRestriction:
    """LocationBase (direct) -> PreciseLocation (restriction) -> GeoFence -> MonitoredGeoFence."""

    def test_precise_location_restricts_location_base(self, rendered_html):
        """PreciseLocation redeclares latitude, longitude, altitude but drops description, accuracy."""
        content = _get_type_template(rendered_html, "type-contents", NS + "PreciseLocation")
        assert "latitude" in content
        assert "longitude" in content
        assert "altitude" in content

    def test_geo_fence_inherits_from_precise_location(self, rendered_html):
        """GeoFence extends PreciseLocation; elements are inside restriction node."""
        inherited = _get_inherited_from(
            rendered_html, NS + "GeoFence", NS + "PreciseLocation"
        )
        assert "latitude" in inherited
        assert "longitude" in inherited
        assert "altitude" in inherited

    def test_geo_fence_does_not_inherit_dropped_elements(self, rendered_html):
        """description and accuracy were restricted away by PreciseLocation."""
        inherited = _get_inherited_from(
            rendered_html, NS + "GeoFence", NS + "PreciseLocation"
        )
        assert "description" not in inherited
        assert "accuracy" not in inherited

    def test_geo_fence_own_elements(self, rendered_html):
        own = _get_own_element_names(rendered_html, NS + "GeoFence")
        assert "radiusMetres" in own

    def test_monitored_geo_fence_inherits_from_geo_fence(self, rendered_html):
        """Two-level chain crossing restriction then extension."""
        inherited = _get_inherited_from(
            rendered_html, NS + "MonitoredGeoFence", NS + "GeoFence"
        )
        assert "radiusMetres" in inherited

    def test_monitored_geo_fence_inherits_from_precise_location_transitively(self, rendered_html):
        """Transitive: MonitoredGeoFence -> GeoFence -> PreciseLocation.
        GeoFence's template shows PreciseLocation's elements."""
        inherited = _get_inherited_from(
            rendered_html, NS + "GeoFence", NS + "PreciseLocation"
        )
        assert "latitude" in inherited
        assert "longitude" in inherited
        assert "altitude" in inherited

    def test_monitored_geo_fence_own_elements(self, rendered_html):
        own = _get_own_element_names(rendered_html, NS + "MonitoredGeoFence")
        assert "monitoringInterval" in own
        assert "alertEndpoint" in own


# ===================================================================
# Case 4: Multi-level chain mixing all three patterns
# ===================================================================


class TestCase4MixedChain:
    """SensorBase (direct) -> TemperatureSensor (ext) -> CalibratedTempSensor (restr) -> HighAccuracySensor (ext)."""

    def test_temperature_sensor_inherits_from_sensor_base(self, rendered_html):
        inherited = _get_inherited_from(
            rendered_html, NS + "TemperatureSensor", NS + "SensorBase"
        )
        assert "sensorId" in inherited
        assert "installDate" in inherited

    def test_temperature_sensor_own_elements(self, rendered_html):
        own = _get_own_element_names(rendered_html, NS + "TemperatureSensor")
        assert "unit" in own
        assert "precision" in own
        assert "minTemp" in own
        assert "maxTemp" in own

    def test_calibrated_temp_sensor_content(self, rendered_html):
        """CalibratedTempSensor restricts TemperatureSensor, redeclaring a subset."""
        content = _get_type_template(
            rendered_html, "type-contents", NS + "CalibratedTempSensor"
        )
        assert "sensorId" in content
        assert "installDate" in content
        assert "unit" in content
        assert "precision" in content

    def test_calibrated_temp_sensor_drops_elements(self, rendered_html):
        """minTemp and maxTemp should not appear in CalibratedTempSensor's own content."""
        own = _get_own_element_names(rendered_html, NS + "CalibratedTempSensor")
        assert "minTemp" not in own
        assert "maxTemp" not in own

    def test_high_accuracy_sensor_inherits_from_calibrated(self, rendered_html):
        """Elements from CalibratedTempSensor's restriction node must be inherited."""
        inherited = _get_inherited_from(
            rendered_html, NS + "HighAccuracySensor", NS + "CalibratedTempSensor"
        )
        assert "sensorId" in inherited
        assert "installDate" in inherited
        assert "unit" in inherited
        assert "precision" in inherited

    def test_high_accuracy_sensor_does_not_inherit_dropped(self, rendered_html):
        inherited = _get_inherited_from(
            rendered_html, NS + "HighAccuracySensor", NS + "CalibratedTempSensor"
        )
        assert "minTemp" not in inherited
        assert "maxTemp" not in inherited

    def test_high_accuracy_sensor_own_elements(self, rendered_html):
        own = _get_own_element_names(rendered_html, NS + "HighAccuracySensor")
        assert "calibrationCertificate" in own
        assert "lastCalibrationDate" in own


# ===================================================================
# Case 5: simpleContent/extension (attribute-only)
# ===================================================================


class TestCase5SimpleContentExtension:
    """MeasurementValue (simpleContent/ext) -> TimestampedMeasurement (simpleContent/ext)."""

    def test_measurement_value_has_attribute(self, rendered_html):
        content = _get_type_template(rendered_html, "type-attrs", NS + "MeasurementValue")
        assert "unitOfMeasure" in content

    def test_timestamped_measurement_has_own_attributes(self, rendered_html):
        content = _get_type_template(rendered_html, "type-attrs", NS + "TimestampedMeasurement")
        assert "timestamp" in content

    def test_timestamped_measurement_type_renders(self, rendered_html):
        """Ensure the type renders without errors (simpleContent chain)."""
        content = _get_type_template(
            rendered_html, "type-contents", NS + "TimestampedMeasurement"
        )
        assert content is not None
