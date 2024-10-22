"""
Panasonic ERJ-6EN Part Number Generator

This script generates all possible part numbers for the Panasonic ERJ-6EN
resistor series based on both E96 and E24 standard resistance values.

Specifications:
Size: 0805 inch (2012 metric)
Power Rating: 0.125W
Resistance Range: 10Ω to 2.2MΩ
Series and Tolerances:
- E96: ±1% (F)
- E24: ±5% (J) [Note: Only 1% (F) tolerance available for values > 1MΩ]
Packaging Options:
- V: Embossed Carrier Tape
"""

import csv
from typing import List, NamedTuple, Final, Iterator
from enum import Enum
import kicad_resistor_symbol_generator as ki_rsg


class SeriesType(Enum):
    """Enumeration for resistor series types."""
    E96 = "E96"
    E24 = "E24"


class PartInfo(NamedTuple):
    """Structure to hold component part information."""
    symbol_name: str
    reference: str
    value: float
    footprint: str
    datasheet: str
    description: str
    manufacturer: str
    mpn: str
    tolerance: str
    voltage_rating: str
    case_code_in: str
    case_code_mm: str


# Constants
BASE_SERIES: Final[str] = "ERJ-6EN"
FOOTPRINT: Final[str] = "footprints:R_0805_2012Metric"
MANUFACTURER: Final[str] = "Panasonic"
DATASHEET: Final[str] = (
    "https://industrial.panasonic.com/cdbs/www-data/pdf/"
    "RDA0000/AOA0000C304.pdf"
)
VOLTAGE_RATING: Final[str] = "150V"
CASE_CODE_IN: Final[str] = "0805"
CASE_CODE_MM: Final[str] = "2012"

E96_BASE_VALUES: Final[List[float]] = [
    10.0, 10.2, 10.5, 10.7, 11.0, 11.3, 11.5, 11.8, 12.1, 12.4, 12.7, 13.0,
    13.3, 13.7, 14.0, 14.3, 14.7, 15.0, 15.4, 15.8, 16.2, 16.5, 16.9, 17.4,
    17.8, 18.2, 18.7, 19.1, 19.6, 20.0, 20.5, 21.0, 21.5, 22.1, 22.6, 23.2,
    23.7, 24.3, 24.9, 25.5, 26.1, 26.7, 27.4, 28.0, 28.7, 29.4, 30.1, 30.9,
    31.6, 32.4, 33.2, 34.0, 34.8, 35.7, 36.5, 37.4, 38.3, 39.2, 40.2, 41.2,
    42.2, 43.2, 44.2, 45.3, 46.4, 47.5, 48.7, 49.9, 51.1, 52.3, 53.6, 54.9,
    56.2, 57.6, 59.0, 60.4, 61.9, 63.4, 64.9, 66.5, 68.1, 69.8, 71.5, 73.2,
    75.0, 76.8, 78.7, 80.6, 82.5, 84.5, 86.6, 88.7, 90.9, 93.1, 95.3, 97.6
]

E24_BASE_VALUES: Final[List[float]] = [
    10.0, 11.0, 12.0, 13.0, 15.0, 16.0, 18.0, 20.0, 22.0, 24.0, 27.0, 30.0,
    33.0, 36.0, 39.0, 43.0, 47.0, 51.0, 56.0, 62.0, 68.0, 75.0, 82.0, 91.0
]

TOLERANCE_MAP: Final[dict[SeriesType, dict[str, str]]] = {
    SeriesType.E96: {'F': '1%'},
    SeriesType.E24: {'J': '5%'}
}

PACKAGING_OPTIONS: Final[List[str]] = ['V']


def format_resistance_value(value: float) -> str:
    """Convert resistance value to a human-readable format."""
    def clean_number(num: float) -> str:
        return f"{num:g}"

    if value >= 1_000_000:
        return f"{clean_number(value / 1_000_000)} MΩ"
    if value >= 1_000:
        return f"{clean_number(value / 1_000)} kΩ"
    return f"{clean_number(value)} Ω"


def generate_resistance_code(value: float) -> str:
    """
    Generate the resistance code portion of the Panasonic part number.
    Format: 4 characters total

    For values < 100Ω:
        Use R notation (e.g., 10R0 for 10Ω, 10R2 for 10.2Ω)

    For values ≥ 100Ω:
        First 3 digits: significant digits
        Last digit: multiplier where:
            0 = ×1 (100-999Ω)
            1 = ×10 (1k-9.99kΩ)
            2 = ×100 (10k-99.9kΩ)
            3 = ×1000 (100k-999kΩ)
            4 = ×10000 (1MΩ)
    """
    if value < 10 or value > 2_200_000:
        raise ValueError("Resistance value out of range (10Ω to 2.2MΩ)")

    # Handle values less than 100Ω using R notation
    if value < 100:
        whole = int(value)
        decimal = int(round((value - whole) * 10))
        return f"{whole:02d}R{decimal}"

    # For values ≥ 100Ω, determine multiplier and significant digits
    if value < 1000:  # 100-999Ω
        significant = int(round(value))
        multiplier = "0"
    elif value < 10000:  # 1k-9.99kΩ
        significant = int(round(value / 10))
        multiplier = "1"
    elif value < 100000:  # 10k-99.9kΩ
        significant = int(round(value / 100))
        multiplier = "2"
    elif value < 1000000:  # 100k-999kΩ
        significant = int(round(value / 1000))
        multiplier = "3"
    else:  # 1MΩ-2.2MΩ
        significant = int(round(value / 10000))
        multiplier = "4"

    return f"{significant:03d}{multiplier}"


def generate_resistance_values(base_values: List[float]) -> Iterator[float]:
    """Generate all valid resistance values from base values."""
    for base_value in base_values:
        current_value = base_value
        while current_value <= 2_200_000:
            if current_value >= 10:
                yield current_value
            current_value *= 10


def create_part_info(
    value: float,
    tolerance_code: str,
    tolerance_value: str,
    packaging: str
) -> PartInfo:
    """Create a PartInfo instance for given parameters."""
    resistance_code = generate_resistance_code(value)
    mpn = f"{BASE_SERIES}{tolerance_code}{resistance_code}{packaging}"
    symbol_name = f"R_{mpn}"
    description = (
        f"RES SMD {format_resistance_value(value)} "
        f"{tolerance_value} 0805 {VOLTAGE_RATING}"
    )

    return PartInfo(
        symbol_name=symbol_name,
        reference="R",
        value=value,
        footprint=FOOTPRINT,
        datasheet=DATASHEET,
        description=description,
        manufacturer=MANUFACTURER,
        mpn=mpn,
        tolerance=tolerance_value,
        voltage_rating=VOLTAGE_RATING,
        case_code_in=CASE_CODE_IN,
        case_code_mm=CASE_CODE_MM
    )


def generate_part_numbers() -> List[PartInfo]:
    """Generate all possible part numbers for both E96 and E24 series."""
    part_numbers: List[PartInfo] = []

    for series_type in SeriesType:
        base_values = (
            E96_BASE_VALUES if series_type == SeriesType.E96
            else E24_BASE_VALUES
        )

        for value in generate_resistance_values(base_values):
            if value <= 2_200_000:  # Ensure we don't exceed maximum resistance
                # For values over 1MΩ, only generate F (1%) tolerance parts
                if value > 1_000_000:
                    tolerance_codes = {'F': '1%'}
                else:
                    tolerance_codes = TOLERANCE_MAP[series_type]

                for tolerance_code, tolerance_value in tolerance_codes.items():
                    for packaging in PACKAGING_OPTIONS:
                        part_numbers.append(create_part_info(
                            value,
                            tolerance_code,
                            tolerance_value,
                            packaging
                        ))

    return part_numbers


def write_to_csv(
    part_numbers: List[PartInfo],
    filename: str = 'ERJ6EN_part_numbers.csv',
    encoding: str = 'utf-8'
) -> None:
    """Write the generated part numbers to a CSV file."""
    headers: Final[List[str]] = [
        'Symbol Name', 'Reference', 'Value', 'Footprint', 'Datasheet',
        'Description', 'Manufacturer', 'MPN', 'Tolerance', 'Voltage Rating',
        'Case Code - in', 'Case Code - mm'
    ]

    with open(filename, 'w', newline='', encoding=encoding) as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)

        for part_info in part_numbers:
            writer.writerow([
                part_info.symbol_name,
                part_info.reference,
                format_resistance_value(part_info.value),
                part_info.footprint,
                part_info.datasheet,
                part_info.description,
                part_info.manufacturer,
                part_info.mpn,
                part_info.tolerance,
                part_info.voltage_rating,
                part_info.case_code_in,
                part_info.case_code_mm
            ])


if __name__ == "__main__":
    generated_part_numbers: List[PartInfo] = generate_part_numbers()
    write_to_csv(generated_part_numbers)
    print(
        f"Generated {len(generated_part_numbers)} part numbers "
        "in 'ERJ6EN_part_numbers.csv'"
    )
    file_pairs = [
        ('ERJ6EN_part_numbers.csv', 'RESISTORS_ERJ6EN_DATA_BASE.kicad_sym')
    ]

    for input_csv, output_symbol in file_pairs:
        try:
            ki_rsg.generate_kicad_symbol(input_csv, output_symbol)
            print(
                f"KiCad symbol file '{output_symbol}' generated successfully.")
        except FileNotFoundError:
            print(f"Error: Input CSV file '{input_csv}' not found.")
        except csv.Error as e:
            print(f"Error reading CSV file '{input_csv}': {e}")
        except IOError as e:
            print(f"Error writing to output file '{output_symbol}': {e}")