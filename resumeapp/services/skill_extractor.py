"""
Skill Extractor Service for AI Resume Analysis.
Uses comprehensive regex pattern dictionaries and domain mapping
to accurately extract technical and soft skills without false positives.
"""

import re

# Comprehensive dictionary of technical skills and their canonical display names
SKILL_PATTERNS = {
    # Programming Languages
    'Python': r'\bpython(?:3)?\b',
    'Java': r'\bjava\b(?!script)',
    'C++': r'(?<![a-zA-Z0-9#+])c\+\+(?![#+a-zA-Z])',
    'C#': r'(?<![a-zA-Z0-9#+])c#(?![#+a-zA-Z])|\bc-sharp\b|\bc\s*sharp\b',
    'C': (
        r'\bc\s+(?:programming|language|developer|compiler)\b|'
        r'\b(?:ansi\s+)?c\s+(?:compiler|code)\b|'
        r'\bembedded\s+c\b|'
        r'\bc\s*[/]\s*c\+\+|\bc\+\+\s*[/]\s*c\b|'
        r'\bc\s+(?:and|&)\s+c\+\+(?![a-zA-Z0-9#+])|\bc\+\+\s+(?:and|&)\s+c\b|'
        r'\b(?:python|java|c\+\+|sql|javascript|typescript|c#|rust|go|html|css)\s*,\s*c\s*[,.\n]|'
        r'\bc\s*,\s*(?:python|java|c\+\+|sql|rust|go|javascript|c#)\b|'
        r'\b(?:languages?|programming(?:\s+languages?)?)\s*:[^.\n]*?\bc\b'
    ),
    'JavaScript': r'\bjavascript\b|\bjs\b(?!on)',
    'TypeScript': r'\btypescript\b|\bts\b',
    'PHP': r'\bphp(?:7|8)?\b',
    'Ruby': r'\bruby\b',
    'Go': (
        r'\bgolang\b|'
        r'\bgo\s+(?:programming|language|developer|dev)\b|'
        r'\b(?:python|java|c\+\+|rust|docker|kubernetes|aws|sql)\s*(?:[,/]|and|&)\s*go\b|'
        r'\bgo\s*(?:[,/]|and|&)\s*(?:ruby|python|rust|docker|kubernetes|sql|c\+\+)\b|'
        r'\b(?:languages?|technologies)\s*:[^.\n]*?\bgo\b'
    ),
    'Rust': r'\brust\b',
    'Swift': r'\bswift\b',
    'Kotlin': r'\bkotlin\b',
    'R': (
        r'\br\s+(?:programming|language)\b|\br\s*studio\b|'
        r'\b(?:python|sql|julia|sas|spss|matlab)\s*(?:[,/]|and|&)\s*r\b|'
        r'\br\s*(?:[,/]|and|&)\s*(?:python|sql|julia|sas|spss|matlab)\b|'
        r'\b(?:languages?|statistical\s+tools?)\s*:[^.\n]*?\br\b'
    ),
    
    # Web & Frameworks
    'Django': r'\bdjango\b',
    'Flask': r'\bflask\b',
    'FastAPI': r'\bfastapi\b',
    'HTML': r'\bhtml(?:5)?\b',
    'CSS': r'\bcss(?:3)?\b',
    'Bootstrap': r'\bbootstrap(?:5)?\b',
    'Tailwind CSS': r'\btailwind(?:\s*css)?\b',
    'React': r'\breact(?:\.js|js)?\b',
    'Node.js': r'\bnode(?:\.js|js)?\b',
    'Express.js': r'\bexpress(?:\.js|js)?\b',
    'Angular': r'\bangular(?:\.js|js)?\b',
    'Vue.js': r'\bvue(?:\.js|js)?\b',
    'Spring Boot': r'\bspring\s*boot\b|\bspring\s+framework\b',
    
    # Databases & Storage
    'SQL': r'(?<!my)(?<!postgre)\bsql\b(?!ite)',
    'MySQL': r'\bmysql\b',
    'PostgreSQL': r'\bpostgres(?:ql)?\b',
    'SQLite': r'\bsqlite(?:3)?\b',
    'MongoDB': r'\bmongodb\b|\bmongo\b',
    'Redis': r'\bredis\b',
    'Oracle': r'\boracle\s*(?:db|database)?\b',
    
    # Data Science, ML & AI
    'Machine Learning': (
        r'\bmachine\s*learning\b|'
        r'\bml\s+(?:model|algorithm|pipeline|engineer|project|system|technique|method)s?\b|'
        r'\b(?:ai|nlp|dl)\s*(?:[,/]|&|and)\s*ml\b|'
        r'\bml\s*(?:[,/]|&|and)\s*(?:ai|nlp|dl)\b'
    ),
    'Deep Learning': (
        r'\bdeep\s*learning\b|'
        r'\bdl\s+(?:model|network|algorithm|engineer|system|framework)s?\b|'
        r'\b(?:ai|nlp|ml)\s*(?:[,/]|&|and)\s*dl\b|'
        r'\bdl\s*(?:[,/]|&|and)\s*(?:ai|nlp|ml)\b'
    ),
    'Natural Language Processing': r'\bnatural\s*language\s*processing\b|\bnlp\b',
    'Data Science': r'\bdata\s*science\b',
    'Pandas': r'\bpandas\b',
    'NumPy': r'\bnumpy\b',
    'Scikit-Learn': r'\bscikit-learn\b|\bsklearn\b',
    'TensorFlow': r'\btensorflow\b|\btf\b',
    'PyTorch': r'\bpytorch\b',
    'Keras': r'\bkeras\b',
    'OpenCV': r'\bopencv\b',
    'Data Analysis': r'\bdata\s*analysis\b',
    'Tableau': r'\btableau\b',
    'Power BI': r'\bpower\s*bi\b',
    'Big Data': r'\bbig\s*data\b',
    
    # Cloud, DevOps & Tools
    'Git': r'\bgit\b(?!hub|lab)',
    'GitHub': r'\bgithub\b',
    'GitLab': r'\bgitlab\b',
    'Docker': r'\bdocker\b',
    'Kubernetes': r'\bkubernetes\b|\bk8s\b',
    'AWS': r'\baws\b|\bamazon\s*web\s*services\b',
    'Azure': r'\bazure\b|\bmicrosoft\s*azure\b',
    'Google Cloud': r'\bgcp\b|\bgoogle\s*cloud\b',
    'Linux': r'\blinux\b|\bubuntu\b|\bcentos\b',
    'REST API': r'\brest(?:ful)?\s*api(?:s)?\b',
    'GraphQL': r'\bgraphql\b',
    'CI/CD': r'\bci\/cd\b|\bcontinuous\s*integration\b',
    'Postman': r'\bpostman\b',
    'Jira': r'\bjira\b',
    'Agile': r'\bagile\b|\bscrum\b',
}

# Domain classification for skills
SKILL_CATEGORIES = {
    'Programming Languages': ['Python', 'Java', 'C++', 'C#', 'C', 'JavaScript', 'TypeScript', 'PHP', 'Ruby', 'Go', 'Rust', 'Swift', 'Kotlin', 'R'],
    'Web & Frameworks': ['Django', 'Flask', 'FastAPI', 'HTML', 'CSS', 'Bootstrap', 'Tailwind CSS', 'React', 'Node.js', 'Express.js', 'Angular', 'Vue.js', 'Spring Boot'],
    'Databases': ['SQL', 'MySQL', 'PostgreSQL', 'SQLite', 'MongoDB', 'Redis', 'Oracle'],
    'AI, ML & Data Science': ['Machine Learning', 'Deep Learning', 'Natural Language Processing', 'Data Science', 'Pandas', 'NumPy', 'Scikit-Learn', 'TensorFlow', 'PyTorch', 'Keras', 'OpenCV', 'Data Analysis', 'Tableau', 'Power BI', 'Big Data'],
    'DevOps, Cloud & Tools': ['Git', 'GitHub', 'GitLab', 'Docker', 'Kubernetes', 'AWS', 'Azure', 'Google Cloud', 'Linux', 'REST API', 'GraphQL', 'CI/CD', 'Postman', 'Jira', 'Agile']
}

def extract_skills_from_text(text):
    """
    Extracts all unique skills recognized in the provided text.
    Returns:
        dict: {
            'skills': list of recognized skill strings,
            'categorized': dict mapping category names to lists of skills,
            'total_count': total number of unique skills found
        }
    """
    if not text:
        return {'skills': [], 'categorized': {}, 'total_count': 0}
        
    lower_text = text.lower()
    extracted = set()
    
    for skill_name, pattern in SKILL_PATTERNS.items():
        if re.search(pattern, lower_text):
            extracted.add(skill_name)
            
    # Sort alphabetically
    skills_list = sorted(list(extracted))
    
    # Categorize skills
    categorized = {}
    for cat_name, skill_members in SKILL_CATEGORIES.items():
        matched = [s for s in skills_list if s in skill_members]
        if matched:
            categorized[cat_name] = matched
            
    return {
        'skills': skills_list,
        'categorized': categorized,
        'total_count': len(skills_list)
    }


def compare_with_job_description(resume_skills, job_description_text, resume_text=""):
    """
    Compares resume skills against the skills extracted from a target job description.
    Also computes optional semantic TF-IDF cosine similarity using scikit-learn.
    Returns:
        dict: {
            'job_skills': list of skills demanded in the job description,
            'matched_skills': list of skills present in both,
            'missing_skills': list of skills in job description but missing in resume,
            'match_percentage': float percentage (0-100),
            'semantic_similarity': float percentage (0-100) or None
        }
    """
    if not job_description_text:
        return {
            'job_skills': [],
            'matched_skills': [],
            'missing_skills': [],
            'match_percentage': 0.0,
            'semantic_similarity': 0.0
        }
        
    jd_extraction = extract_skills_from_text(job_description_text)
    jd_skills = jd_extraction['skills']
    
    resume_skills_set = set(resume_skills)
    jd_skills_set = set(jd_skills)
    
    matched = sorted(list(resume_skills_set.intersection(jd_skills_set)))
    missing = sorted(list(jd_skills_set.difference(resume_skills_set)))
    
    if jd_skills_set:
        match_percentage = round((len(matched) / len(jd_skills_set)) * 100, 1)
    else:
        match_percentage = 0.0

    # Optional Machine Learning TF-IDF feature extraction & cosine similarity
    semantic_similarity = 0.0
    if resume_text and job_description_text:
        try:
            from ml.feature_extractor import ResumeFeatureExtractor
            extractor = ResumeFeatureExtractor()
            semantic_similarity = extractor.compute_similarity(resume_text, job_description_text)
        except Exception:
            semantic_similarity = 0.0
        
    return {
        'job_skills': jd_skills,
        'matched_skills': matched,
        'missing_skills': missing,
        'match_percentage': match_percentage,
        'semantic_similarity': semantic_similarity
    }
