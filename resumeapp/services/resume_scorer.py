"""
Resume Scoring Engine for AI Resume Analysis.
Calculates a transparent, multi-dimensional score (0 - 100) based on
structural completeness, skill richness, and job description alignment.
"""

def compute_resume_score(raw_text, detected_sections, extracted_skills, jd_comparison=None):
    """
    Computes a transparent score from 0 to 100 with clear component points:
    1. Section Structure (max 30 pts)
    2. Skill Richness & Diversity (max 35 pts)
    3. Document Length & Completeness (max 15 pts)
    4. Job Description Alignment (max 20 pts)
    """
    word_count = len(raw_text.split()) if raw_text else 0
    section_count = len(detected_sections)
    skill_count = len(extracted_skills)
    
    # --- 1. Section Structure (max 30 points) ---
    # Standard sections: Contact, Summary, Experience, Education, Skills, Projects
    key_sections = ['Technical Skills', 'Education', 'Work Experience', 'Projects', 'Contact Information', 'Professional Summary']
    present_key_sections = [s for s in key_sections if s in detected_sections]
    section_points = min(30, len(present_key_sections) * 5)
    
    # --- 2. Skill Richness & Diversity (max 35 points) ---
    if skill_count >= 12:
        skill_points = 35
    elif skill_count >= 8:
        skill_points = 28
    elif skill_count >= 5:
        skill_points = 20
    elif skill_count >= 3:
        skill_points = 14
    elif skill_count >= 1:
        skill_points = 8
    else:
        skill_points = 0
        
    # --- 3. Document Length & Completeness (max 15 points) ---
    # Standard 1-2 page resumes typically have 250 - 900 words
    if 250 <= word_count <= 1000:
        length_points = 15
    elif 150 <= word_count < 250:
        length_points = 10
    elif word_count > 1000:
        length_points = 10  # Slightly long
    elif word_count > 50:
        length_points = 5
    elif word_count > 0:
        length_points = 2
    else:
        length_points = 0
        
    # --- 4. Job Alignment or General Content Richness (max 20 points) ---
    has_jd = jd_comparison is not None and len(jd_comparison.get('job_skills', [])) > 0
    if has_jd:
        match_pct = jd_comparison.get('match_percentage', 0.0)
        jd_points = int(round((match_pct / 100.0) * 20))
    else:
        # If no job description is provided, allocate points based on overall section completeness
        if section_count >= 5 and skill_count >= 6:
            jd_points = 20
        elif section_count >= 4 or skill_count >= 4:
            jd_points = 14
        elif section_count >= 1 or skill_count >= 1:
            jd_points = 8
        else:
            jd_points = 0
            
    total_score = min(100, max(0, section_points + skill_points + length_points + jd_points))
    
    # Breakdown details
    breakdown = {
        'sections_score': section_points,
        'sections_max': 30,
        'skills_score': skill_points,
        'skills_max': 35,
        'length_score': length_points,
        'length_max': 15,
        'alignment_score': jd_points,
        'alignment_max': 20,
        'has_job_description': has_jd,
        'semantic_similarity': jd_comparison.get('semantic_similarity', 0.0) if jd_comparison else 0.0,
        'word_count': word_count
    }
    
    # Generate Strengths
    strengths = []
    if section_points >= 25:
        strengths.append(f"Strong structural organization with {len(present_key_sections)} standard sections detected.")
    if skill_points >= 28:
        strengths.append(f"Broad technical skill profile with {skill_count} relevant technical keywords.")
    if length_points == 15:
        strengths.append(f"Optimal document length ({word_count} words) suitable for standard 1-2 page screening.")
    if has_jd and breakdown['alignment_score'] >= 14:
        strengths.append(f"High alignment with the target job description ({jd_comparison.get('match_percentage')}% matched).")
    if not strengths and total_score > 0:
        strengths.append("Basic resume content successfully parsed and indexed.")
        
    # Generate Improvements
    improvements = []
    missing_sections = [s for s in key_sections if s not in detected_sections]
    if missing_sections:
        improvements.append(f"Consider adding missing standard sections: {', '.join(missing_sections[:3])}.")
    if skill_count < 6:
        improvements.append("Increase technical keywords by specifying tools, languages, and frameworks used in your projects.")
    if 0 < word_count < 250:
        improvements.append(f"Resume appears concise ({word_count} words). Elaborate on project deliverables and quantifiable achievements.")
    elif word_count > 1000:
        improvements.append(f"Resume is somewhat lengthy ({word_count} words). Aim for a focused 1-2 page presentation.")
    elif word_count == 0:
        improvements.append("Resume contains no readable text content. Ensure document has selectable text.")
    if has_jd and jd_comparison.get('missing_skills'):
        missing_preview = ", ".join(jd_comparison['missing_skills'][:4])
        improvements.append(f"Target role requires skills missing from your resume: {missing_preview}.")
    if not improvements:
        improvements.append("Your resume meets all standard formatting and structural best practices.")
        
    return {
        'total_score': total_score,
        'breakdown': breakdown,
        'strengths': strengths,
        'improvements': improvements,
        'explanation': (
            f"Overall score of {total_score}/100 calculated from: Structure ({section_points}/30), "
            f"Skill Richness ({skill_points}/35), Formatting/Length ({length_points}/15), "
            f"and Alignment ({jd_points}/20)."
        ),
        'disclaimer': (
            "Note: This score is an automated analytical metric based on resume keyword presence, "
            "standard section formatting, and requirement overlap. It does not guarantee employment or represent a proprietary corporate ATS."
        )
    }
