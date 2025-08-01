"""
GST State Codes Mapping for India
"""

# Complete GST state code mapping
STATE_CODE_MAPPING = {
    # States
    'Andhra Pradesh': '37',
    'Arunachal Pradesh': '12',
    'Assam': '18',
    'Bihar': '10',
    'Chhattisgarh': '22',
    'Goa': '30',
    'Gujarat': '24',
    'Haryana': '06',
    'Himachal Pradesh': '02',
    'Jharkhand': '20',
    'Karnataka': '29',
    'Kerala': '32',
    'Madhya Pradesh': '23',
    'Maharashtra': '27',
    'Manipur': '14',
    'Meghalaya': '17',
    'Mizoram': '15',
    'Nagaland': '13',
    'Odisha': '21',
    'Punjab': '03',
    'Rajasthan': '08',
    'Sikkim': '11',
    'Tamil Nadu': '33',
    'Telangana': '36',
    'Tripura': '16',
    'Uttar Pradesh': '09',
    'Uttarakhand': '05',
    'West Bengal': '19',
    
    # Union Territories
    'Andaman and Nicobar Islands': '35',
    'Chandigarh': '04',
    'Dadra and Nagar Haveli and Daman and Diu': '26',
    'Delhi': '07',
    'Jammu and Kashmir': '01',
    'Ladakh': '38',
    'Lakshadweep': '31',
    'Puducherry': '34',
    
    # Common variations
    'A&N Islands': '35',
    'D&N Haveli': '26',
    'J&K': '01',
    'NCT Delhi': '07',
    'Pondicherry': '34',
    
    # Handle case variations
    'andhra pradesh': '37',
    'ANDHRA PRADESH': '37',
    'delhi': '07',
    'DELHI': '07',
    'rajasthan': '08',
    'RAJASTHAN': '08',
    'maharashtra': '27',
    'MAHARASHTRA': '27',
    'karnataka': '29',
    'KARNATAKA': '29',
    'tamil nadu': '33',
    'TAMIL NADU': '33',
    'gujarat': '24',
    'GUJARAT': '24',
    'uttar pradesh': '09',
    'UTTAR PRADESH': '09',
    'west bengal': '19',
    'WEST BENGAL': '19',
    'kerala': '32',
    'KERALA': '32'
}


def get_state_code(state_name: str) -> str:
    """
    Get GST state code from state name
    Returns '00' if state not found
    """
    if not state_name:
        return '00'
    
    # First try exact match
    if state_name in STATE_CODE_MAPPING:
        return STATE_CODE_MAPPING[state_name]
    
    # Try case-insensitive match
    state_lower = state_name.lower().strip()
    if state_lower in STATE_CODE_MAPPING:
        return STATE_CODE_MAPPING[state_lower]
    
    # Try title case
    state_title = state_name.title().strip()
    if state_title in STATE_CODE_MAPPING:
        return STATE_CODE_MAPPING[state_title]
    
    # Default fallback
    return '00'


def validate_state_code(state_code: str) -> bool:
    """
    Validate if a state code is valid GST state code
    """
    valid_codes = set(STATE_CODE_MAPPING.values())
    return state_code in valid_codes