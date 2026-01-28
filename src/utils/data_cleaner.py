"""
Utility functions for cleaning and processing lead data
"""
import re
import pandas as pd

def extract_email(text):
    """
    Extract institutional emails (prioritize .edu, .ac., university domains)
    """
    if not text:
        return ""
    
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    
    if emails:
        email = emails[0].lower()
        
        # Priority 1: Institutional emails
        institutional_domains = [
            '.edu', '.ac.', '.uni-', 'university', 'college', 
            'hospital', 'institute', 'research', '.gov', '.org',
            'clinic', 'medical', 'school', 'lab', 'center'
        ]
        
        if any(domain in email for domain in institutional_domains):
            return email
        
        # Priority 2: Company emails (biotech/pharma)
        company_domains = [
            'pharma', 'biotech', 'therapeutics', 'bioscience',
            'bio', 'genetics', 'genomics', 'cell', 'lifescience'
        ]
        
        if any(domain in email for domain in company_domains):
            return email
        
        # Priority 3: Accept some country-specific academic emails
        country_academic = ['.ac.cn', '.ac.jp', '.ac.kr', '.ac.il', '.ac.ir']
        if any(domain in email for domain in country_academic):
            return email
        
        # Last resort: Personal emails (keep but flag as lower quality)
        personal_domains = ['gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com']
        if any(domain in email for domain in personal_domains):
            return email  # Keep for now
    
    return ""

def extract_location(affiliation):
    """
    Extract clean city/country location from affiliation with SMART guessing
    """
    if not affiliation:
        return ""
    
    affiliation_lower = affiliation.lower()
    
    # 1. DIRECT UNIVERSITY-TO-CITY MAPPING (Most Accurate)
    university_city_map = {
        # US Universities
        'harvard': 'Boston, MA, USA',
        'stanford': 'Stanford, CA, USA',
        'mit': 'Cambridge, MA, USA',
        'caltech': 'Pasadena, CA, USA',
        'princeton': 'Princeton, NJ, USA',
        'yale': 'New Haven, CT, USA',
        'columbia': 'New York, NY, USA',
        'uchicago': 'Chicago, IL, USA',
        'upenn': 'Philadelphia, PA, USA',
        'johns hopkins': 'Baltimore, MD, USA',
        'duke': 'Durham, NC, USA',
        'cornell': 'Ithaca, NY, USA',
        'northwestern': 'Evanston, IL, USA',
        'washington university': 'St. Louis, MO, USA',
        'vanderbilt': 'Nashville, TN, USA',
        'emory': 'Atlanta, GA, USA',
        'university of california': 'California, USA',
        'uc berkeley': 'Berkeley, CA, USA',
        'ucla': 'Los Angeles, CA, USA',
        'usc': 'Los Angeles, CA, USA',
        'university of michigan': 'Ann Arbor, MI, USA',
        'university of texas': 'Austin, TX, USA',
        'university of washington': 'Seattle, WA, USA',
        'university of illinois': 'Urbana, IL, USA',
        'illinois urbana': 'Urbana, IL, USA',
        'university of florida': 'Gainesville, FL, USA',
        'university of colorado': 'Denver, CO, USA',
        'university of southern california': 'Los Angeles, CA, USA',
        'university of tennessee': 'Knoxville, TN, USA',
        'university of notre dame': 'Notre Dame, IN, USA',
        'university of virginia': 'Charlottesville, VA, USA',
        'university of wisconsin': 'Madison, WI, USA',
        'university of minnesota': 'Minneapolis, MN, USA',
        
        # UK Universities
        'oxford': 'Oxford, UK',
        'cambridge': 'Cambridge, UK',
        'imperial college': 'London, UK',
        'ucl': 'London, UK',
        'kings college': 'London, UK',
        'london school': 'London, UK',
        'manchester': 'Manchester, UK',
        'edinburgh': 'Edinburgh, UK',
        'bristol': 'Bristol, UK',
        'glasgow': 'Glasgow, UK',
        'birmingham': 'Birmingham, UK',
        'leeds': 'Leeds, UK',
        'sheffield': 'Sheffield, UK',
        'liverpool': 'Liverpool, UK',
        
        # European Universities
        'eth zurich': 'Zurich, Switzerland',
        'karolinska': 'Stockholm, Sweden',
        'university of copenhagen': 'Copenhagen, Denmark',
        'copenhagen university': 'Copenhagen, Denmark',
        'lund university': 'Lund, Sweden',
        'radboud university': 'Nijmegen, Netherlands',
        'kuleuven': 'Leuven, Belgium',
        'university of amsterdam': 'Amsterdam, Netherlands',
        'university of helsinki': 'Helsinki, Finland',
        'university of oslo': 'Oslo, Norway',
        
        # Asian Universities
        'university of tokyo': 'Tokyo, Japan',
        'kyoto university': 'Kyoto, Japan',
        'tokyo university': 'Tokyo, Japan',
        'tsinghua university': 'Beijing, China',
        'peking university': 'Beijing, China',
        'zhejiang university': 'Hangzhou, China',
        'shanghai jiao tong': 'Shanghai, China',
        'fudan university': 'Shanghai, China',
        'nankai university': 'Tianjin, China',
        'wuhan university': 'Wuhan, China',
        'university of hong kong': 'Hong Kong, China',
        'national university of singapore': 'Singapore',
        'seoul national university': 'Seoul, South Korea',
        'korea university': 'Seoul, South Korea',
        'yonsei university': 'Seoul, South Korea',
        'chung-ang university': 'Seoul, South Korea',
        'ang university': 'Seoul, South Korea',  # Short form
        'university of guilan': 'Rasht, Iran',
        'guilan university': 'Rasht, Iran',
        'university of tehran': 'Tehran, Iran',
        
        # Chinese Research Institutes
        'shenzhen institutes': 'Shenzhen, China',
        'siat': 'Shenzhen, China',
        'chinese academy of sciences': 'Beijing, China',
        'cas': 'Beijing, China',
        
        # Specific from your data
        'university of technology': 'Shijiazhuang, China',
        'research center for human tissue': 'Shenzhen, China',
        'ningbo university': 'Ningbo, China',
        'jinan university': 'Guangzhou, China',
        'southeast university': 'Nanjing, China',
        'hee university': 'Seoul, South Korea',
    }
    
    # Check for known universities first (most accurate)
    for uni_keyword, city in university_city_map.items():
        if uni_keyword in affiliation_lower:
            return city
    
    # 2. EXTRACT CITY, STATE/COUNTRY PATTERNS
    patterns = [
        # City, State (USA): "Boston, MA"
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z]{2})\b',
        
        # City, Country: "London, UK" or "Paris, France"
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
        
        # University of City: "University of Chicago"
        r'\b(?:University|College|Institute|School)\s+(?:of|at|in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
        
        # City University: "Boston University"
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:University|College|Institute)\b',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, affiliation, re.IGNORECASE)
        if match:
            city = match.group(1)
            if len(match.groups()) > 1:
                region = match.group(2)
                # Add USA if it's a state abbreviation
                if len(region) == 2 and region.isupper():
                    return f"{city}, {region}, USA"
                else:
                    return f"{city}, {region}"
            return f"{city}"
    
    # 3. FIND COMMON CITY NAMES
    common_cities = [
        'Boston', 'Cambridge', 'San Francisco', 'New York', 'Chicago', 'Los Angeles',
        'Philadelphia', 'Baltimore', 'Seattle', 'Houston', 'Atlanta', 'Durham',
        'London', 'Oxford', 'Manchester', 'Edinburgh', 'Bristol', 'Glasgow',
        'Paris', 'Lyon', 'Marseille', 'Berlin', 'Munich', 'Frankfurt', 'Hamburg',
        'Zurich', 'Geneva', 'Basel', 'Stockholm', 'Uppsala', 'Copenhagen', 'Oslo',
        'Tokyo', 'Kyoto', 'Osaka', 'Beijing', 'Shanghai', 'Hong Kong', 'Singapore',
        'Sydney', 'Melbourne', 'Toronto', 'Vancouver', 'Montreal', 'Seoul',
        'Mumbai', 'Delhi', 'Bangalore', 'Moscow', 'Saint Petersburg', 'Warsaw',
        'Madrid', 'Barcelona', 'Rome', 'Milan', 'Vienna', 'Prague', 'Budapest'
    ]
    
    for city in common_cities:
        if city.lower() in affiliation_lower:
            # Add country if obvious
            if city in ['Boston', 'Cambridge', 'San Francisco', 'New York', 'Chicago']:
                return f"{city}, USA"
            elif city in ['London', 'Oxford', 'Cambridge', 'Manchester']:
                return f"{city}, UK"
            elif city in ['Tokyo', 'Kyoto', 'Osaka']:
                return f"{city}, Japan"
            elif city in ['Beijing', 'Shanghai', 'Hong Kong']:
                return f"{city}, China"
            elif city in ['Seoul']:
                return f"{city}, South Korea"
            else:
                return city
    
    # 4. GET COUNTRY FROM TEXT
    countries = {
        'usa': 'USA', 'united states': 'USA', 'america': 'USA',
        'uk': 'UK', 'united kingdom': 'UK', 'britain': 'UK', 'england': 'UK',
        'china': 'China', 'chinese': 'China',
        'japan': 'Japan', 'japanese': 'Japan',
        'korea': 'South Korea', 'korean': 'South Korea',
        'germany': 'Germany', 'german': 'Germany',
        'france': 'France', 'french': 'France',
        'italy': 'Italy', 'italian': 'Italy',
        'spain': 'Spain', 'spanish': 'Spain',
        'canada': 'Canada', 'canadian': 'Canada',
        'australia': 'Australia', 'australian': 'Australia',
        'india': 'India', 'indian': 'India',
        'brazil': 'Brazil', 'brazilian': 'Brazil',
        'russia': 'Russia', 'russian': 'Russia',
        'iran': 'Iran', 'persian': 'Iran',
        'israel': 'Israel', 'israeli': 'Israel',
        'sweden': 'Sweden', 'swedish': 'Sweden',
        'denmark': 'Denmark', 'danish': 'Denmark',
        'norway': 'Norway', 'norwegian': 'Norway',
        'finland': 'Finland', 'finnish': 'Finland',
        'netherlands': 'Netherlands', 'dutch': 'Netherlands',
        'switzerland': 'Switzerland', 'swiss': 'Switzerland',
        'belgium': 'Belgium', 'belgian': 'Belgium',
    }
    
    for country_keyword, country_name in countries.items():
        if country_keyword in affiliation_lower:
            return country_name
    
    # 5. LAST RESORT: Get first capitalized word that's not a common academic term
    words = affiliation.split()
    skip_words = {
        'university', 'college', 'institute', 'center', 'centre', 'department',
        'school', 'laboratory', 'lab', 'research', 'science', 'sciences',
        'technology', 'medical', 'medicine', 'health', 'national', 'international',
        'faculty', 'division', 'unit', 'program', 'group', 'team', 'section',
        'office', 'campus', 'biomolecular', 'engineering', 'biology', 'systems',
        'cell', 'molecular', 'chemical', 'physical', 'clinical', 'bio', 'tissue',
        'organ', 'human', 'animal', 'plant', 'development', 'studies', 'hospital',
        'clinic', 'academy', 'foundation', 'corporation', 'incorporated', 'limited'
    }
    
    for word in words:
        clean_word = word.strip('.,;:()[]{}').title()
        if (clean_word and len(clean_word) > 2 and clean_word[0].isupper() and
            clean_word.lower() not in skip_words and not clean_word.isdigit()):
            return clean_word
    
    return "Unknown"

def clean_name(name):
    """
    Clean and format author names
    """
    if not name:
        return ""
    
    # Remove academic titles and degrees
    name = re.sub(r'\b(Ph\.?D\.?|M\.?D\.?|Prof\.?|Dr\.?|Mr\.?|Mrs\.?|Ms\.?)\b', '', name, flags=re.IGNORECASE)
    
    # Remove extra spaces and clean up
    name = ' '.join(name.split())
    
    return name.title()

def extract_company(affiliation):
    """
    Extract company/university name from affiliation
    """
    if not affiliation:
        return ""
    
    # Remove location info and clean
    affiliation_clean = re.sub(r',\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$', '', affiliation)
    affiliation_clean = re.sub(r'\s+[A-Z]{2,3}\s*,?\s*(?:USA|UK|U\.S\.A\.?)?$', '', affiliation_clean)
    
    # Extract university/company name
    patterns = [
        r'^(.*?)(?:\s+(?:University|College|Institute|School|Center|Centre|Hospital|Clinic))',
        r'\b(University of [A-Za-z\s]+)\b',
        r'\b([A-Z][a-z]+ (?:University|College|Institute))\b',
        r'\b([A-Z][a-z]+ (?:Inc\.?|LLC|Ltd\.?|Corp\.?|Pharmaceuticals|Technologies|Biosciences?|Biotech))\b',
        r'\b([A-Z][a-z]+ (?:Research|Science|Medical|Health) (?:Center|Centre|Institute|Foundation))\b',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, affiliation_clean, re.IGNORECASE)
        if match:
            result = match.group(1).strip()
            if result:
                return result
    
    # Return first meaningful part
    parts = [p.strip() for p in affiliation_clean.split(',')]
    return parts[0] if parts else "Unknown"