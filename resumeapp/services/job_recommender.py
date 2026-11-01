"""
Job and Career Recommendation Service for AI Resume Analysis.
Maps extracted candidate skills to industry career tracks and roles,
calculating skill match percentages and explaining rationale transparently.
"""

# Benchmark skill profiles for key industry career categories
CAREER_PROFILES = {
    'Python Developer': {
        'core_skills': ['Python', 'Django', 'Flask', 'FastAPI', 'SQL', 'PostgreSQL', 'MySQL', 'Git', 'REST API', 'Docker'],
        'description': 'Focuses on designing, building, and deploying backend applications and APIs using Python.'
    },
    'Web Developer': {
        'core_skills': ['HTML', 'CSS', 'JavaScript', 'TypeScript', 'Bootstrap', 'React', 'Node.js', 'Git', 'REST API', 'Tailwind CSS'],
        'description': 'Builds responsive front-end interfaces, client-side functionality, and integrated web applications.'
    },
    'Backend Developer': {
        'core_skills': ['Python', 'Java', 'Django', 'Spring Boot', 'Node.js', 'SQL', 'MySQL', 'PostgreSQL', 'Redis', 'Docker', 'REST API'],
        'description': 'Architects server-side logic, database schemas, performance scaling, and secure API gateways.'
    },
    'Data Analyst': {
        'core_skills': ['SQL', 'Python', 'Excel', 'Tableau', 'Power BI', 'Pandas', 'NumPy', 'Data Analysis', 'MySQL'],
        'description': 'Extracts, transforms, and visualizes structured data to drive business intelligence and insights.'
    },
    'Data Scientist': {
        'core_skills': ['Python', 'R', 'Pandas', 'NumPy', 'Scikit-Learn', 'Machine Learning', 'SQL', 'Data Science', 'Data Analysis'],
        'description': 'Leverages statistical modeling, experimental design, and predictive algorithms on complex data.'
    },
    'Machine Learning Engineer': {
        'core_skills': ['Python', 'Machine Learning', 'Deep Learning', 'Scikit-Learn', 'TensorFlow', 'PyTorch', 'NumPy', 'Docker', 'Git'],
        'description': 'Engineers machine learning pipelines, trains neural networks, and deploys scalable models in production.'
    },
    'AI Engineer': {
        'core_skills': ['Python', 'Deep Learning', 'Natural Language Processing', 'TensorFlow', 'PyTorch', 'OpenCV', 'Keras', 'Docker'],
        'description': 'Develops intelligent AI systems focusing on Generative AI, computer vision, and NLP applications.'
    }
}

def recommend_career_paths(extracted_skills):
    """
    Evaluates candidate skills against benchmark career tracks.
    Returns:
        list of dicts containing:
            - role_title: name of career category
            - match_percentage: percentage of core skills matched (0 - 100)
            - matched_skills: list of skills matching this role
            - missing_skills: recommended skills to acquire for this track
            - description: role overview
            - rationale: clear explanation of the recommendation
    """
    if not extracted_skills:
        # Default starter recommendation if no skills detected
        return [{
            'role_title': 'Junior Software Developer',
            'match_percentage': 0,
            'matched_skills': [],
            'missing_skills': ['Python', 'Git', 'SQL', 'HTML', 'CSS'],
            'description': 'Entry-level software development covering core programming fundamentals.',
            'rationale': 'No technical keywords detected in resume yet. Start by listing foundational programming skills.'
        }]
        
    candidate_skills_set = set(extracted_skills)
    results = []
    
    for role_title, data in CAREER_PROFILES.items():
        core_set = set(data['core_skills'])
        matched = sorted(list(candidate_skills_set.intersection(core_set)))
        missing = sorted(list(core_set.difference(candidate_skills_set)))
        
        match_pct = round((len(matched) / len(core_set)) * 100, 1) if core_set else 0.0
        
        if matched:
            rationale = (
                f"Matches {len(matched)} core competencies: {', '.join(matched)}. "
                f"Acquiring {', '.join(missing[:3])} will make you a competitive candidate for this role."
            )
        else:
            rationale = (
                f"Currently 0 direct keyword matches. Recommended skills to enter this path: {', '.join(missing[:4])}."
            )
            
        results.append({
            'role_title': role_title,
            'match_percentage': match_pct,
            'matched_skills': matched,
            'missing_skills': missing,
            'description': data['description'],
            'rationale': rationale
        })
        
    # Sort recommendations by highest match percentage first
    results.sort(key=lambda x: x['match_percentage'], reverse=True)
    return results
