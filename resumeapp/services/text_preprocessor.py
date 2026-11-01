"""
Text Preprocessor and Section Detector for AI Resume Analysis.
Normalizes text while preserving crucial programming language symbols (e.g., C++, C#, .NET).
"""

import re
import unicodedata

# Common sections found in standard professional resumes
RESUME_SECTIONS = {
    'Contact Information': [
        r'^(?:contact(?:\s+information|\s+details)?|personal\s+details)$',
        r'\bcontact\s*:',
        r'\b(?:email|phone|linkedin|github)\s*:'
    ],
    'Professional Summary': [
        r'^(?:professional\s+summary|executive\s+summary|summary|profile|career\s+objective|objective|about\s+me)$'
    ],
    'Work Experience': [
        r'^(?:work\s+experience|professional\s+experience|experience|employment\s+history|work\s+history|career\s+history|internships?)$'
    ],
    'Education': [
        r'^(?:education(?:\s+(?:and\s+qualifications|details))?|academic\s+background|academics?|educational\s+qualifications?|qualifications?|degrees?)$'
    ],
    'Technical Skills': [
        r'^(?:technical\s+skills?|core\s+skills?|key\s+skills?|skills?\s*(?:&|and)\s*technologies|skills?\s*(?:&|and)\s*competencies|skills?|technologies|tools\s*&\s*technologies|proficiencies)$'
    ],
    'Projects': [
        r'^(?:projects?|key\s+projects?|personal\s+projects?|academic\s+projects?|selected\s+projects?)$'
    ],
    'Certifications & Achievements': [
        r'^(?:certifications?|certificates?|achievements?|awards?(?:\s*&\s*honors)?|licenses?)$'
    ]
}

def clean_and_normalize_text(raw_text):
    """
    Cleans raw text by normalizing unicode characters, removing unreadable glyphs,
    and collapsing multiple blank lines and spaces.
    """
    if not raw_text:
        return ""
    
    # Normalize unicode characters (NFKD form)
    text = unicodedata.normalize('NFKD', raw_text)
    
    # Replace non-breaking spaces and tabs
    text = text.replace('\xa0', ' ').replace('\t', ' ')
    
    # Remove carriage returns
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Collapse multiple consecutive whitespaces on the same line
    lines = [re.sub(r'[ ]{2,}', ' ', line).strip() for line in text.split('\n')]
    
    # Filter out excessive blank lines (maximum 1 blank line between text chunks)
    collapsed_lines = []
    prev_blank = False
    for line in lines:
        if line:
            collapsed_lines.append(line)
            prev_blank = False
        elif not prev_blank:
            collapsed_lines.append('')
            prev_blank = True
            
    return '\n'.join(collapsed_lines).strip()


def detect_sections(text):
    """
    Detects which standard resume sections are present in the resume.
    Ensures headings are actual standalone titles or marked headers,
    preventing body text words (e.g., 'experience', 'college') from triggering false matches.
    """
    if not text:
        return []
        
    detected = set()
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Check lines for heading patterns
    for idx, raw_line in enumerate(lines):
        # Normalize line by removing leading markdown, bullets, numbering, or trailing colons
        clean_line = re.sub(r'^[#*\-•\s\d\.\)]+', '', raw_line).strip()
        clean_line_no_colon = clean_line.rstrip(':').strip().lower()
        word_count = len(clean_line.split())
        
        # Section titles in resumes are concise headings (typically 1 to 5 words)
        is_heading_candidate = 0 < word_count <= 5 and len(clean_line) <= 60
        
        # Check contact info in header area (first 8 lines)
        if idx < 8:
            lower_raw = raw_line.lower()
            if any(k in lower_raw for k in ['contact:', 'phone:', 'email:', 'linkedin.com', 'github.com', '| contact:']):
                detected.add('Contact Information')
                
        for section_name, patterns in RESUME_SECTIONS.items():
            if section_name in detected:
                continue
                
            for pattern in patterns:
                # 1. Match against standalone clean heading line
                if is_heading_candidate and re.search(pattern, clean_line_no_colon):
                    detected.add(section_name)
                    break
                # 2. Match lines with explicit trailing colon (e.g., "Work Experience:")
                elif raw_line.rstrip().endswith(':') and is_heading_candidate and re.search(pattern, clean_line_no_colon):
                    detected.add(section_name)
                    break
                # 3. Match explicit all-caps isolated headers
                elif raw_line.isupper() and is_heading_candidate and re.search(pattern, clean_line_no_colon):
                    detected.add(section_name)
                    break
                    
    # Maintain consistent presentation order
    ordered = [s for s in RESUME_SECTIONS.keys() if s in detected]
    return ordered


def tokenize_words(text):
    """
    Tokenizes text into words while keeping technical terms intact.
    Preserves terms like c++, c#, .net, node.js.
    """
    # Pattern to match technical terms like c++, c#, .net, or words with hyphens
    tokens = re.findall(r'[a-zA-Z0-9+#\.\-]+', text)
    return [t.lower() for t in tokens if len(t) > 1]
