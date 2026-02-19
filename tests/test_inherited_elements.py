"""Tests for inherited element rendering across different complexType patterns.

Uses samples/inherited_elements_demo.xsd which covers:
  Case 1: Direct children (always worked)
  Case 2: complexContent/extension (issue #6)
  Case 3: complexContent/restriction
  Case 4: Multi-level chain mixing all three patterns
  Case 5: simpleContent/extension (attribute-only)
"""

import pytest
from conftest import (
    SAMPLES_DIR,
    extract_element_names,
    get_template,
    inner_html,
    parse_html,
)

XSD_FILE = SAMPLES_DIR / "inherited_elements_demo.xsd"

# The demo schema declares targetNamespace with prefix "tns", so all type names
# in the rendered HTML are prefixed with "tns:" (e.g. "tns:Dog").
NS = "tns:"


@pytest.fixture(scope="module")
def doc():
    """Generate HTML from the demo XSD and return it as a parsed lxml document."""
    from xsd_browser.main import render_html

    html = render_html(XSD_FILE, minify=False)
    return parse_html(html)


def _get_inherited_from(doc, type_name: str, base_name: str) -> list[str]:
    """Get element names inherited from a specific base type."""
    tmpl = get_template(doc, "type-contents", type_name)
    # Find the inherited-section div that links to the base type
    sections = tmpl.xpath('.//div[@class="inherited-section"]')
    for section in sections:
        if section.xpath(f'.//a[contains(@href, "#type-{base_name}")]'):
            return extract_element_names(section)
    return []


def _get_all_inherited_element_names(doc, type_name: str) -> list[str]:
    """Get all element names shown in inherited sections for a type."""
    tmpl = get_template(doc, "type-contents", type_name)
    inherited_sections = tmpl.xpath('.//div[@class="inherited-section"]')
    names = []
    for section in inherited_sections:
        names.extend(extract_element_names(section))
    return names


def _get_own_element_names(doc, type_name: str) -> list[str]:
    """Get element names defined directly by the type (not inside inherited sections)."""
    tmpl = get_template(doc, "type-contents", type_name)
    # Elements NOT inside an inherited-section
    all_refs = tmpl.xpath('.//xbe-collapsible-element-ref')
    inherited_refs = tmpl.xpath('.//div[@class="inherited-section"]//xbe-collapsible-element-ref')
    inherited_set = set(id(r) for r in inherited_refs)
    return [r.get('element') for r in all_refs if id(r) not in inherited_set]


# ===================================================================
# Case 1: Direct children (always worked)
# ===================================================================


class TestCase1DirectChildren:
    """AnimalBase (direct) -> Dog (extension) -> ServiceDog (extension)."""

    def test_dog_inherits_from_animal_base(self, doc):
        inherited = _get_all_inherited_element_names(doc, NS + "Dog")
        assert "name" in inherited
        assert "species" in inherited

    def test_dog_own_elements(self, doc):
        own = _get_own_element_names(doc, NS + "Dog")
        assert "breed" in own

    def test_service_dog_inherits_breed_from_dog(self, doc):
        """This is the key test: breed lives inside Dog's extension node."""
        inherited = _get_inherited_from(doc, NS + "ServiceDog", NS + "Dog")
        assert "breed" in inherited

    def test_service_dog_inherits_from_animal_base_transitively(self, doc):
        """Transitive: ServiceDog -> Dog -> AnimalBase. Dog's template shows AnimalBase's elements."""
        inherited = _get_all_inherited_element_names(doc, NS + "Dog")
        assert "name" in inherited
        assert "species" in inherited

    def test_service_dog_own_elements(self, doc):
        own = _get_own_element_names(doc, NS + "ServiceDog")
        assert "certificationId" in own
        assert "handler" in own


# ===================================================================
# Case 2: complexContent/extension (issue #6)
# ===================================================================


class TestCase2ComplexContentExtension:
    """VehicleBase (direct) -> Car (extension) -> ElectricCar (extension)."""

    def test_car_inherits_from_vehicle_base(self, doc):
        inherited = _get_inherited_from(doc, NS + "Car", NS + "VehicleBase")
        assert "vin" in inherited
        assert "manufacturer" in inherited
        assert "yearOfManufacture" in inherited

    def test_car_own_elements(self, doc):
        own = _get_own_element_names(doc, NS + "Car")
        assert "numberOfDoors" in own
        assert "trunkCapacityLitre" in own

    def test_electric_car_inherits_from_car(self, doc):
        """Core issue #6 test: Car's elements are inside complexContent/extension."""
        inherited = _get_inherited_from(doc, NS + "ElectricCar", NS + "Car")
        assert "numberOfDoors" in inherited
        assert "trunkCapacityLitre" in inherited

    def test_electric_car_inherits_from_vehicle_base_transitively(self, doc):
        """Transitive: ElectricCar -> Car -> VehicleBase. Car's template shows VehicleBase's elements."""
        inherited = _get_inherited_from(doc, NS + "Car", NS + "VehicleBase")
        assert "vin" in inherited
        assert "manufacturer" in inherited
        assert "yearOfManufacture" in inherited

    def test_electric_car_own_elements(self, doc):
        own = _get_own_element_names(doc, NS + "ElectricCar")
        assert "batteryCapacityKWh" in own
        assert "rangeKm" in own
        assert "chargingStandard" in own


# ===================================================================
# Case 3: complexContent/restriction
# ===================================================================


class TestCase3ComplexContentRestriction:
    """LocationBase (direct) -> PreciseLocation (restriction) -> GeoFence -> MonitoredGeoFence."""

    def test_precise_location_restricts_location_base(self, doc):
        """PreciseLocation redeclares latitude, longitude, altitude but drops description, accuracy."""
        tmpl = get_template(doc, "type-contents", NS + "PreciseLocation")
        content = inner_html(tmpl)
        assert "latitude" in content
        assert "longitude" in content
        assert "altitude" in content

    def test_geo_fence_inherits_from_precise_location(self, doc):
        """GeoFence extends PreciseLocation; elements are inside restriction node."""
        inherited = _get_inherited_from(doc, NS + "GeoFence", NS + "PreciseLocation")
        assert "latitude" in inherited
        assert "longitude" in inherited
        assert "altitude" in inherited

    def test_geo_fence_does_not_inherit_dropped_elements(self, doc):
        """description and accuracy were restricted away by PreciseLocation."""
        inherited = _get_inherited_from(doc, NS + "GeoFence", NS + "PreciseLocation")
        assert "description" not in inherited
        assert "accuracy" not in inherited

    def test_geo_fence_own_elements(self, doc):
        own = _get_own_element_names(doc, NS + "GeoFence")
        assert "radiusMetres" in own

    def test_monitored_geo_fence_inherits_from_geo_fence(self, doc):
        """Two-level chain crossing restriction then extension."""
        inherited = _get_inherited_from(doc, NS + "MonitoredGeoFence", NS + "GeoFence")
        assert "radiusMetres" in inherited

    def test_monitored_geo_fence_inherits_from_precise_location_transitively(self, doc):
        """Transitive: MonitoredGeoFence -> GeoFence -> PreciseLocation.
        GeoFence's template shows PreciseLocation's elements."""
        inherited = _get_inherited_from(doc, NS + "GeoFence", NS + "PreciseLocation")
        assert "latitude" in inherited
        assert "longitude" in inherited
        assert "altitude" in inherited

    def test_monitored_geo_fence_own_elements(self, doc):
        own = _get_own_element_names(doc, NS + "MonitoredGeoFence")
        assert "monitoringInterval" in own
        assert "alertEndpoint" in own


# ===================================================================
# Case 4: Multi-level chain mixing all three patterns
# ===================================================================


class TestCase4MixedChain:
    """SensorBase (direct) -> TemperatureSensor (ext) -> CalibratedTempSensor (restr) -> HighAccuracySensor (ext)."""

    def test_temperature_sensor_inherits_from_sensor_base(self, doc):
        inherited = _get_inherited_from(doc, NS + "TemperatureSensor", NS + "SensorBase")
        assert "sensorId" in inherited
        assert "installDate" in inherited

    def test_temperature_sensor_own_elements(self, doc):
        own = _get_own_element_names(doc, NS + "TemperatureSensor")
        assert "unit" in own
        assert "precision" in own
        assert "minTemp" in own
        assert "maxTemp" in own

    def test_calibrated_temp_sensor_content(self, doc):
        """CalibratedTempSensor restricts TemperatureSensor, redeclaring a subset."""
        tmpl = get_template(doc, "type-contents", NS + "CalibratedTempSensor")
        content = inner_html(tmpl)
        assert "sensorId" in content
        assert "installDate" in content
        assert "unit" in content
        assert "precision" in content

    def test_calibrated_temp_sensor_drops_elements(self, doc):
        """minTemp and maxTemp should not appear in CalibratedTempSensor's own content."""
        own = _get_own_element_names(doc, NS + "CalibratedTempSensor")
        assert "minTemp" not in own
        assert "maxTemp" not in own

    def test_high_accuracy_sensor_inherits_from_calibrated(self, doc):
        """Elements from CalibratedTempSensor's restriction node must be inherited."""
        inherited = _get_inherited_from(
            doc, NS + "HighAccuracySensor", NS + "CalibratedTempSensor"
        )
        assert "sensorId" in inherited
        assert "installDate" in inherited
        assert "unit" in inherited
        assert "precision" in inherited

    def test_high_accuracy_sensor_does_not_inherit_dropped(self, doc):
        inherited = _get_inherited_from(
            doc, NS + "HighAccuracySensor", NS + "CalibratedTempSensor"
        )
        assert "minTemp" not in inherited
        assert "maxTemp" not in inherited

    def test_high_accuracy_sensor_own_elements(self, doc):
        own = _get_own_element_names(doc, NS + "HighAccuracySensor")
        assert "calibrationCertificate" in own
        assert "lastCalibrationDate" in own


# ===================================================================
# Case 5: simpleContent/extension (attribute-only)
# ===================================================================


class TestCase5SimpleContentExtension:
    """MeasurementValue (simpleContent/ext) -> TimestampedMeasurement (simpleContent/ext)."""

    def test_measurement_value_has_attribute(self, doc):
        tmpl = get_template(doc, "type-attrs", NS + "MeasurementValue")
        content = inner_html(tmpl)
        assert "unitOfMeasure" in content

    def test_timestamped_measurement_has_own_attributes(self, doc):
        tmpl = get_template(doc, "type-attrs", NS + "TimestampedMeasurement")
        content = inner_html(tmpl)
        assert "timestamp" in content

    def test_timestamped_measurement_type_renders(self, doc):
        """Ensure the type renders without errors (simpleContent chain)."""
        tmpl = get_template(doc, "type-contents", NS + "TimestampedMeasurement")
        assert tmpl is not None
