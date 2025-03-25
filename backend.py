import pandas as pd
import re
import streamlit as st



def detect_oil_type(supplier_text):
    oil_type_mapping = {
        r"\bAN\b": ("Dry Type", "2"), r"\bAF\b": ("Dry Type", "2"), r"\bANAF\b": ("Dry Type", "2"), r"\bANAN\b": ("Dry Type", "2"),
        r"\bAA\b": ("Dry Type", "2"),  # Added AA as Dry Type
        r"\bAFWF\b": ("Gas Filled", "4"),
        r"\bKFWF\b": ("Ester Oil", "1"), r"\bKNAF\b": ("Ester Oil", "1"), r"\bKNAN\b": ("Ester Oil", "1"),
        r"\bODAF\b": ("Mineral Oil", "0"), r"\bOFAF\b": ("Mineral Oil", "0"), r"\bOFAN\b": ("Mineral Oil", "0"), r"\bOFWF\b": ("Mineral Oil", "0"),
        r"\bONAF\b": ("Mineral Oil", "0"), r"\bONAN\b": ("Mineral Oil", "0"), r"\bONWN\b": ("Mineral Oil", "0")
    }

    #supplier_text_upper = re.sub(r'\s+', '', supplier_text.upper())  # Remove spaces & convert to uppercase
    supplier_text_upper = re.sub(r'[^A-Za-z0-9]', ' ', supplier_text.upper()).strip()
    supplier_text_upper = re.sub(r'\s+', ' ', supplier_text_upper).strip()
    attributes = {}  # Ensure attributes dictionary exists

    for pattern, (oil_type, code) in oil_type_mapping.items():
        if re.search(pattern, supplier_text_upper, re.IGNORECASE):
            attributes["Oil/Dry"] = (oil_type, code)
            return attributes

    special_cases = {
        "FR3": ("Ester Oil", "1"),
        "CAST RESIN": ("Cast Resin Dry", "5"),
        "RESIBLOC": ("Cast Resin Dry", "5"),
        "VPI": ("VPI Dry", "3"),
        "VACUUMPRESSUREIMPREGNATION": ("VPI Dry", "3"),
        "DRY": ("Dry Type", "2"),
        "AA": ("Dry Type", "2"),
        "OILFILLED": ("Mineral Oil", "0"),
         "AFWF": ("Gas Filled", "4"),
         "ESTER": ("Ester Oil", "1"),
        "MINERAL": ("Mineral Oil", "0"),
        "GASFILLED": ("Gas Filled", "4")
    }

    for keyword, (oil_type, code) in special_cases.items():
        if keyword in supplier_text_upper:
            attributes["Oil/Dry"] = (oil_type, code)
            return attributes

    

    attributes["Oil/Dry"] = ("Mineral Oil", "0")  # Default to Mineral Oil
    return attributes



def detect_application_type(text):
    """Detects application type from text. Defaults to 'Land Based' if not specified."""
    attributes = {}
    application_types = {
        r"land\s*based": ("Land Based", "0"),
        r"offshore|off-shore": ("Offshore", "1"),
        r"o&g\s*onshore|onshore|on-shore": ("O&G Onshore", "2"),
        r"atex": ("Atex", "3")
    }
    
    text_lower = text.lower() if text else ""

    for pattern, (app_type, code) in application_types.items():
        if re.search(pattern, text_lower, re.IGNORECASE):
            attributes["Application"] = (app_type, code)
            return attributes  # Stops at the first match
    
    attributes["Application"] = ("Land based", "0")  # Default if no match is found
    return attributes


def detect_tap_changer(text):
    """Detect tap changer type: OLTC (On-Load Tap Changer) or DTC (De-Energized Tap Changer), updating an attributes dictionary."""
    attributes = {}
    
    if not text or text.strip() == "":
        attributes["Tap Changer"] = ("De-Energized Tap Changer", "0")  # Default to DTC if nothing is specified
        return attributes
    
    text_lower = text.lower()
    
    # Patterns for OLTC (On-Load Tap Changer)
    oltc_patterns = [
        r'\boltc\b', r'\boltp\b', r'on\s*-?load', r'onload',
        r'on\s*-?load\s*-?tap', r'on\s*-?load\s*-?tap\s*-?changer',
        r'\bon\s*load\b', r'\bon[-\s]?load\b', r'\bon[-\s]?load[-\s]?tap\b',
        r'on\s*load\s*changer', r'load\s*tap\s*changer', r'\bon\s*load\s*tap\s*changer\b'
    ]
    
    # Patterns for DTC (De-Energized Tap Changer)
    dtc_patterns = [
        r'\bdtc\b', r'\bdetc\b', r'\bdenergized\b', r'de[-\s]?energized', r'degenerized',
        r'off\s*-?load', r'off\s*-?load\s*-?tap', r'off\s*-?load\s*-?tap\s*-?changer',
        r'\boff\s*load\b', r'\boff[-\s]?load[-\s]?tap\b', r'off\s*load\s*changer'
    ]
    
    # Check for OLTC match
    if any(re.search(pattern, text_lower) for pattern in oltc_patterns):
        attributes["Tap Changer"] = ("On Load Tap Changer", "1")
        return attributes
    
    # Check for DTC match
    if any(re.search(pattern, text_lower) for pattern in dtc_patterns):
        attributes["Tap Changer"] = ("De-Energized Tap Changer", "0")
        return attributes
    
    # Default case (if no match found)
    attributes["Tap Changer"] = ("De-Energized Tap Changer", "0")
    return attributes




def convert_v_to_kv(value):
    """Convert voltage from V to kV if necessary"""
    value = float(value)
    return round(value / 1000, 3) if value >= 100 else round(value, 3)

def extract_primary_voltage(text):
    patterns = [
        # 1. Three-slash kV values (e.g., "10/20/30kV" -> 10 kV)
        (re.compile(r'\b(\d+(?:[.,]\d+)?)\s*(?:kV|KV|kv)?(?:\s*/\s*|\s+|-)(\d+(?:[.,]\d+)?)\s*(?:kV|KV|kv)?(?:\s*/\s*|\s+)(\d+(?:[.,]\d+)?)\s*(?:kV|KV|kv)\b',re.IGNORECASE),
        lambda m: max(float(m.group(i).replace(',', '.')) for i in range(1, 4) if m.group(i))),

       (re.compile(r'\(?\b(\d+(?:[.,]\d+)?)\s*(?:kV|KV|kv)?\s*(?:/|\s|-|to|TO|To|~~|~)\s*(\d+(?:[.,]\d+)?)\s*(?:kV|KV|kv)\b\)?',re.IGNORECASE),
        lambda m: max(float(m.group(1).replace(',', '.')), float(m.group(2).replace(',', '.')))),

        
        # 10. Standalone kV value (e.g., "275kV" -> 275 kV)
        (re.compile(r'\b(?:Primary|primary voltage)\s*(\d+(?:[.,]\d+)?)\s*kV\b(?!A)', re.IGNORECASE), 
        lambda m: float(m.group(1).replace(',', '.'))),

        # Extracts highest kV from "XX/YY kV" but prevents matching "XX YY kV" (no separator)
        ( re.compile(
        r'\b(?:Pri|Max)?[:\s]*'
        r'(\d+(?:[.,]\d+)?(?:[eE][+-]?\d+)?)\s*(kV|KV|kv|V|v|volts|VOLTS|Volts|Volts)?'
        r'\s*(?:,?\s*\d{1,3}\s*(?:Hz|HZ|hz|Phase|PH)?,?\s*)?'
        r'(?:/|-|to|→|~~|~)\s*'
        r'(?:Sec|Min)?[:\s]*'
        r'(\d+(?:[.,]\d+)?(?:[eE][+-]?\d+)?)\s*(kV|KV|kv|V|v|volts|VOLTS|Volts|Volts)\b',re.IGNORECASE),        
        (lambda m: max(
         float(m.group(1).replace(',', '.')) if m.group(2) and 'kV' in m.group(2).lower() else convert_v_to_kv(float(m.group(1).replace(',', '.'))),
         float(m.group(3).replace(',', '.')) if 'kV' in m.group(4).lower() else convert_v_to_kv(float(m.group(3).replace(',', '.'))))      if m and m.group(4) else None)),  # Ensure match exists and group(4) is present
       

        

        
        # 3. Highest voltage in V/kV and convert if necessary (e.g., "10000V/4160V" -> 10 kV)
       (re.compile(r'\(?\b(\d+(?:[.,]\d+)?)\s*(?:V|v|volt|volts|Volts|Volts)?\s*(?:/|\s|-|to|To|TO)\s*(\d+(?:[.,]\d+)?)\s*(?:V|v|volt|volts|Volts|Volts)\b',re.IGNORECASE),
        lambda m: convert_v_to_kv(max(float(m.group(1).replace(',', '.')), float(m.group(2).replace(',', '.'))))),

        
        # 4. Special case handling for "kV ± ..." patterns (e.g., "6,3 kV ± 2 x 2,5 % / 330 V" -> 6.3 kV)
        (re.compile(r'\b(\d+(?:[.,]\d+)?)\s*kV\s*[±\-]',re.IGNORECASE), 
         lambda m: float(m.group(1).replace(',', '.'))),
        
        # 5. Standalone V value - Convert to kV, ensuring it is not part of another structure
        (re.compile(r'\b(\d+(?:[.,]\d+)?)\s*[Vv]\b(?!.*kV)'), 
         lambda m: convert_v_to_kv(float(m.group(1).replace(',', '.')))),

        
        # 6. Primary voltage in V - Convert to kV (e.g., "Primary 14400V" -> 14.4 kV)
        (re.compile(r'\bPrimary\s*(\d+(?:[.,]\d+)?)\s*V\b'), 
         lambda m: convert_v_to_kv(float(m.group(1).replace(',', '.')))),

        
        # 7. HV voltage in V - Convert to kV (e.g., "HV 690 V" -> 0.69 kV)
        (re.compile(r'HV\s*(\d+(?:\.\d+)?)\s*(?:\[V\]|V)',re.IGNORECASE), 
         lambda m: convert_v_to_kv(float(m.group(1).replace(',', '.')))),

        
        # 8. HV voltage in kV - Extract directly (e.g., "HV [20kV]" -> 20 kV)
        (re.compile(r'HV\s*(\d+(?:\.[,]\d+)?)\s*(?:\[kV\]|kV)',re.IGNORECASE), 
         lambda m: float(m.group(1).replace(',', '.'))),
        
        # 9. HV voltage in V - Convert to kV (e.g., "HV [20V]" -> 20 kV)
        (re.compile(r'HV\s*(\d+(?:\.[,]\d+)?)\s*(?:\[V\]|V)'), 
         lambda m: convert_v_to_kv(float(m.group(1).replace(',', '.')))),
        
        # 10. Standalone kV value (e.g., "275kV" -> 275 kV)
        (re.compile(r'\bPrimary\s*(\d+(?:[.,]\d+)?)\s*kV\b(?!A)'), 
         lambda m: float(m.group(1).replace(',', '.'))),
        
        # 11. Extract highest value from mixed format "V/kV" cases (e.g., "20000/2x502V" -> 20 kV)
        (re.compile(r'\b(\d+(?:[.,]\d+)?)\s*/\s*(?:\d+x)?(\d+(?:[.,]\d+)?)\s*V\b'), 
         lambda m: convert_v_to_kv(max(float(m.group(1).replace(',', '.')), float(m.group(2).replace(',', '.'))))),

       (re.compile(
        r'(\d+(?:\.\d+)?)\s*(?:x|×)\s*10(?:\^|\⁰|\¹|\²|\³|\⁴|\⁵|\⁶|\⁷|\⁸|\⁹)?(\d+)\s*(V|kV|KV|kv|volts|VOLTS)?'
        r'\s*(?:/|-|to|→|~~|~)\s*'
        r'(\d+(?:\.\d+)?)\s*(?:x|×)\s*10(?:\^|\⁰|\¹|\²|\³|\⁴|\⁵|\⁶|\⁷|\⁸|\⁹)?(\d+)\s*(V|kV|KV|kv|volts|VOLTS)'),
        lambda m: max(
        float(m.group(1)) * (10 ** int(m.group(2))) if 'kV' in (m.group(3) or '').lower() else convert_v_to_kv(float(m.group(1)) * (10 ** int(m.group(2)))),
        float(m.group(4)) * (10 ** int(m.group(5))) if 'kV' in (m.group(6) or '').lower() else convert_v_to_kv(float(m.group(4)) * (10 ** int(m.group(5)))))),
        
        # 12. Extract kV values from transformer specifications (e.g., "5330kVA, 20000/2x502V" -> 20 kV)
        (re.compile(r'\b(\d{4,5})\s*/\s*\d+x\d+V\b'),
         lambda m: convert_v_to_kv(float(m.group(1).replace(',', '.')))),

        (re.compile(r'^\s*(\d+(?:[.,]\d+)?)\s*×\s*10(?:\^|\⁰|\¹|\²|\³|\⁴|\⁵|\⁶|\⁷|\⁸|\⁹)?(\d+)\s*(V|kV)(?=\s*/)',re.IGNORECASE),
        lambda m: float(m.group(1).replace(',', '.')) * (10 ** int(m.group(2))) / (1000 if m.group(3).lower() == 'v' else 1))
    ]
    for pattern, func in patterns:
        match = pattern.search(text)
        if match:
            primary_voltage = func(match)
            print(f"Extracted primary voltage: {primary_voltage} kV")
            
            if primary_voltage < 36:
                return "< 36 kV", "0"
            elif 36 <= primary_voltage < 110:
                return "> 36 - 110 kV", "1"
            elif 110 <= primary_voltage < 220:
                return "> 110 - 220 kV", "2"
            else:
                return "> 220 kV", "3"
    
    return "Unknown", ""

    

    
def convert_power(value):
    """Convert various power units to MVA."""
    match = re.search(r'(?:(\d+\.?\d*)\s*\[?)(kVA|MVA|W|kW|KW|VA)(?:\]?)', value, re.IGNORECASE)
    if not match:
        return "Unknown"

    num, unit = match.groups()
    num = float(num)
    unit = unit.lower()

    conversion = {
        "kva": lambda x: x / 1000,    # kVA → MVA
        "mva": lambda x: x,          # Already in MVA
        "w": lambda x: x / 1e6,      # W → MVA
        "kw": lambda x: x / 1000,    # kW → MVA
        "va": lambda x: x / 1e6      # VA → MVA
    }

    converted_value = conversion.get(unit, lambda x: "Unknown")(num)

    if isinstance(converted_value, str):
        return "Unknown"

    return converted_value


def classify_power_range(mva_value):
    """Classify power into predefined ranges."""
    power_ranges = [
        (0, 1, "0 - 1 MVA", "0"),
        (1, 10, "1 - 10 MVA", "1"),
        (10, 50, "10 - 50 MVA", "2"),
        (50, 100, "50 - 100 MVA", "3"),
        (100, 250, "100 - 250 MVA", "4"),
        (250, float('inf'), "> 250 MVA", "5")
    ]
    for lower, upper, description, code in power_ranges:
        if lower <= mva_value < upper:
            return description, code
    return "Unknown", ""

def get_tooltip(value, is_default=False):
    if is_default:
        return f'<span title="This is a default value">{value} ℹ</span>'
    return value


def extract_attributes(supplier_text):
    """Extract key attributes from supplier text using regex and keyword matching."""
    attributes = {
        "Product type": ("Unknown", "X"),
        "Power in MVA": ("Unknown", "X"),
        "Primary Voltage in kV":("Unknown", "X"),
        "Tap Changer": ("De-Energized Tap Changer", "0"),
        "Application": ("Land Based", "0"),
        "System Category": ("Product","A"),
        "Oil/Dry": ("Unknown", "X"),
        "Classification": ("Outdoor","1"),
        "Standard": ("IEC", "0"),
        "Winding material": ("Unknown", "X")
    }
    
    product_types = {
        "transformer": {
            "synonyms": {"transformer", "trans", "transfo", "xfmr", "trafo", "tr", "ppt","x'mer"},
            "category": "02-Transformer",
            "code": "02"
    },
        "switchgear": {
            "synonyms": {"switchgear", "switch board", "switch cabinet", "mv switchgear"},
            "category": "03-MV Switchgear",
            "code": "03"
    },
        "high voltage": {
            "synonyms": {"high voltage", "hv equipment", "hv", "high volt"},
            "category": "04-High Voltage Equipment",
            "code": "04"
    },
        "e-house": {
            "synonyms": {"e-house", "electrical house", "ehouse", "e house"},
            "category": "05-E-House",
            "code": "05"
    },
        "mechanical": {
            "synonyms": {"mechanical", "mech"},
            "category": "11-Mechanical",
            "code": "11"
    },
        "automation": {
            "synonyms": {"automation", "auto", "control system"},
            "category": "01-Automation",
            "code": "01"
    },
        "IT": {
            "synonyms": {"IT", "information technology", "software"},
            "category": "00-IT",
            "code": "00"
    }
}



    supplier_text_lower = supplier_text.lower().strip()
    for key, values in product_types.items():
        if any(word in supplier_text_lower for word in values["synonyms"]):
            attributes["Product type"] = (values["category"], values["code"])
            break
    
    power_match = re.search(r"(?:KVA|MVA|W|kW|KW|VA)\s*[:]?\s*(\d+(?:\.\d+)?)|\b(\d+(?:\.\d+)?)\s*\[?(kVA|MVA|W|kW|KW|VA)\]?", supplier_text, re.IGNORECASE)
    if power_match:
        power_value = power_match.group(1) or power_match.group(2)
        power_unit = power_match.group(3) or "kVA"
        full_power_string = f"{power_value} {power_unit}"
        converted_power = convert_power(full_power_string)
        if isinstance(converted_power, float):
            attributes['Power in MVA'] = classify_power_range(converted_power)
        
    
    voltage_value = extract_primary_voltage(supplier_text)
    if voltage_value[0] != "Unknown":
        attributes['Primary Voltage in kV'] = voltage_value
    
        
    
    tap_changer_value = detect_tap_changer(supplier_text)
    if tap_changer_value.get("Tap Changer", ("Unknown", ""))[0] != "Unknown":
        attributes["Tap Changer"] = tap_changer_value["Tap Changer"]

    
   
    application_attributes = detect_application_type(supplier_text)
    if application_attributes:  # Ensure something was detected
        attributes.update(application_attributes)


    oil_dry_value=detect_oil_type(supplier_text)
    if oil_dry_value:
        attributes.update(oil_dry_value)

    
    if re.search("software", supplier_text, re.IGNORECASE):
        attributes['System Category'] = ("Software","S")
    
    
    classification_types = {
    "indoor": ("Indoor", "0"), "inside": ("Indoor", "0"), "enclosed": ("Indoor", "0"), 
    "internal": ("Indoor", "0"), "sealed": ("Indoor", "0"), "climate controlled": ("Indoor", "0"), 
    "protected location": ("Indoor", "0"),
    
    "outdoor": ("Outdoor", "1"), "external": ("Outdoor", "1"), "outside": ("Outdoor", "1"), 
    "weatherproof": ("Outdoor", "1"), "exposed": ("Outdoor", "1"), "harsh environment": ("Outdoor", "1"), 
    "all-weather": ("Outdoor", "1"), "IP-rated": ("Outdoor", "1"),
    
    "marine": ("Marine", "2"), "offshore": ("Marine", "2"), "shipboard": ("Marine", "2"), 
    "naval": ("Marine", "2"), "seaworthy": ("Marine", "2"), "vessel": ("Marine", "2"), 
    "corrosion-resistant": ("Marine", "2"), "coastal": ("Marine", "2"), "dockside": ("Marine", "2"), 
    "maritime": ("Marine", "2"),
    
    "zone-2": ("Zone-2", "3"), "hazardous area": ("Zone-2", "3"), "explosion-proof": ("Zone-2", "3"), 
    "ex-proof": ("Zone-2", "3"), "atex": ("Zone-2", "3"), "iecex": ("Zone-2", "3"), 
    "intrinsically safe": ("Zone-2", "3"), "flammable environment": ("Zone-2", "3"), 
    "gas group": ("Zone-2", "3"), "class 1 div 2": ("Zone-2", "3"), "oil & gas": ("Zone-2", "3")
}

    for keyword, (classification, code) in classification_types.items():
        if re.search(rf"\b{keyword}\b", supplier_text, re.IGNORECASE):
            attributes['Classification'] = (classification, code)
            break
    

    standard_types = {
    r"iec|international\s*electrotechnical\s*commission|euro\s*standard|en\s*\d{4}": ("IEC", "0"),
    
    r"ansi|american\s*national\s*standards\s*institute|ieee|ul\s*\d{3,4}": ("ANSI", "1"),
    
    r"csa|canadian\s*standards\s*association|csa\s*c\d{2,4}|canadian\s*electrical\s*code": ("CSA", "2"),
    
    r"eac|eurasian\s*economic\s*commission|gost|tr\s*cu|eurasian\s*certification": ("EAC", "3"),
    
    r"jec|japanese\s*electrotechnical\s*committee|jis|japan\s*standard|jec\s*\d{3,4}": ("JEC", "4"),
    
    r"xxx|non\s*standard|custom\s*specification|special\s*design|proprietary\s*standard": ("XXX", "5")
}

    
    for keyword, (standard, code) in standard_types.items():
        if re.search(rf"\b{keyword}\b", supplier_text, re.IGNORECASE):
            attributes['Standard'] = (standard, code)
            break

    if re.search(r"\b(cu|copper|cu\s*winding|copper\s*winding|cu\s*coil|copper\s*coil|cu\s*wire|copper\s*wire|cu\s*conductor|copper\s*conductor|cu\s*foil|copper\s*foil|cu\s*busbar|copper\s*busbar)\b", 
             supplier_text, re.IGNORECASE):
        attributes['Winding material'] = ("Cu", "0")

    elif re.search(r"\b(al|alu|minium|aluminum|aluminium|al\s*winding|aluminum\s*winding|aluminium\s*winding|al\s*coil|aluminum\s*coil|aluminium\s*coil|al\s*wire|aluminum\s*wire|aluminium\s*wire|al\s*conductor|aluminum\s*conductor|aluminium\s*conductor|al\s*foil|aluminum\s*foil|aluminium\s*foil|al\s*busbar|aluminum\s*busbar|aluminium\s*busbar)\b", 
               supplier_text, re.IGNORECASE):
        attributes['Winding material'] = ("Al", "1")


    product_code = "4JZZ" + "".join(val[1] for val in attributes.values())
    
    
    
    return attributes, product_code

def main():
    st.title("Transformer Code Generator")
    st.write("Enter supplier specifications to extract parameters and generate the power code.")



    supplier_text = st.text_area("Sample Description:Oil Distribution Transformer - 2300kVA - 10kV/0.4kV - 60Hz -AL-ONAN-IEC", height=100)

    if st.button("Extract Parameters"):
        if supplier_text:
            attributes, product_code = extract_attributes(supplier_text)

            # Create DataFrame
            df_params = pd.DataFrame(
            [(key, get_tooltip(val[0], len(val) == 3), val[1]) for key, val in attributes.items()],
            columns=["Type", "Parameter", "Code"]
            )

            # Function to Highlight 'X' in Red
            def highlight_x(val):
                return f'<span style="color: red; font-weight: bold;">{val}</span>' if val == "X" else val

            df_params["Code"] = df_params["Code"].apply(highlight_x)

            # Custom CSS to Match Table with Input Width
            st.markdown("""
                <style>
                    .table-container {
                        width: 100%;
                        display: flex;
                        justify-content: center;
                    }
                    table {
                        width: 100%;
                        border-collapse: collapse;
                        text-align: left;
                    }
                    th, td {
                        border: 1px solid #ddd;
                        padding: 2px;
                        text-align: center;
                    }
                    th {
                        background-color: #f4f4f4;
                    }
                </style>
            """, unsafe_allow_html=True)
            st.subheader("Extracted Parameters")

            # Display Table with Matching Width
            st.markdown('<div class="table-container">', unsafe_allow_html=True)
            st.write(df_params.to_html(escape=False), unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Display Generated Product Code
            st.subheader("Generated Product Code  ")
            highlighted_code = re.sub(r'(X+)', r'<span style="color: red; font-weight: bold;">\1</span>', product_code)
            st.markdown(f"<p style='text-align: left; font-size: 20px;'><code>{highlighted_code}</code></p>", unsafe_allow_html=True)

             # Error Message for Missing Data
            if "X" in product_code:
                st.error("⚠️ An error occurred. Defaulting to 'X'. The required data might be missing from the provided description. Please check the input or adjust the data to match the format below.")


        else:
            st.warning("Please enter supplier input.")

if __name__ == "__main__":
    main()
