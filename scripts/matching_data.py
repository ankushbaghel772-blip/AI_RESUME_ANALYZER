"""Download and prepare the explicitly labeled positive pairs for the experiment."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.request import urlopen

import pandas as pd


DATASET_ID = "michaelozon/candidate-matching-synthetic"
DATASET_API = f"https://huggingface.co/api/datasets/{DATASET_ID}"
DATA_FILES = {
    "resumes.parquet": "resumes/train-00000-of-00001.parquet",
    "jobs.parquet": "jobs/train-00000-of-00001.parquet",
    "matches.parquet": "matches/train-00000-of-00001.parquet",
}
EXPECTED_LICENSE = "mit"


def find_project_root(start: Path | None = None) -> Path:
    """Find the Django project root from a notebook or script working directory."""
    current = (start or Path.cwd()).resolve()
    candidates = [current, *current.parents]
    for candidate in candidates:
        if (candidate / "manage.py").is_file() and (candidate / "resumeapp").is_dir():
            return candidate
    raise FileNotFoundError(
        "Could not find the AI_RESUME_ANALYSIS project root. "
        "Start Jupyter from the project directory or a child directory."
    )


def download_source_tables(project_root: Path | None = None) -> dict[str, Path]:
    """Verify the current dataset card declares MIT, then download its three tables."""
    root = (project_root or find_project_root()).resolve()
    raw_dir = root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    with urlopen(DATASET_API, timeout=30) as response:
        metadata = json.load(response)
    card = metadata.get("cardData") or {}
    if metadata.get("private") or metadata.get("gated"):
        raise RuntimeError(f"Dataset {DATASET_ID} is no longer public and ungated.")
    if str(card.get("license", "")).lower() != EXPECTED_LICENSE:
        raise RuntimeError(
            f"Dataset license check failed: expected MIT, found {card.get('license')!r}. "
            "Do not use these files until the license is verified."
        )

    revision = metadata.get("sha")
    if not revision:
        raise RuntimeError("Hugging Face did not return a revision SHA; download stopped.")

    result: dict[str, Path] = {}
    for local_name, repository_path in DATA_FILES.items():
        destination = raw_dir / local_name
        url = f"https://huggingface.co/datasets/{DATASET_ID}/resolve/{revision}/{repository_path}"
        with urlopen(url, timeout=120) as response:
            destination.write_bytes(response.read())
        result[local_name] = destination

    manifest = {
        "dataset_id": DATASET_ID,
        "revision": revision,
        "license": card["license"],
        "source": f"https://huggingface.co/datasets/{DATASET_ID}",
        "files": list(DATA_FILES.values()),
        "label_limitations": (
            "The matches file lists explicitly relevant resumes only and caps the list at 30 per job. "
            "Unlisted pairs are unlabeled; they are not treated as negative examples."
        ),
    }
    (raw_dir / "dataset_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return result


def prepare_positive_pairs(project_root: Path | None = None) -> pd.DataFrame:
    """Join only the source's explicit relevant-resume memberships into text pairs."""
    root = (project_root or find_project_root()).resolve()
    raw_dir = root / "data" / "raw"
    expected = [raw_dir / name for name in DATA_FILES]
    manifest_path = raw_dir / "dataset_manifest.json"
    if not all(path.is_file() for path in expected) or not manifest_path.is_file():
        download_source_tables(root)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("license") != EXPECTED_LICENSE or manifest.get("dataset_id") != DATASET_ID:
        raise RuntimeError("Dataset manifest does not verify the expected MIT-licensed source.")

    resumes = pd.read_parquet(raw_dir / "resumes.parquet")
    jobs = pd.read_parquet(raw_dir / "jobs.parquet")
    matches = pd.read_parquet(raw_dir / "matches.parquet")

    required = {
        "resume_id", "role", "seniority", "years_experience", "industry",
        "education", "skills", "summary", "experience_bullets",
    }
    if not required.issubset(resumes.columns):
        raise ValueError(f"Unexpected resume schema; missing {sorted(required - set(resumes.columns))}.")
    if not {"job_id", "job_title", "seniority", "industry", "must_have_skills",
            "nice_to_have_skills", "description", "responsibilities", "requirements"}.issubset(jobs.columns):
        raise ValueError("Unexpected job schema; required job fields are missing.")
    if not {"job_id", "relevant_resume_ids"}.issubset(matches.columns):
        raise ValueError("Unexpected matches schema; explicit relevant-resume IDs are required.")
    if resumes["resume_id"].duplicated().any() or jobs["job_id"].duplicated().any():
        raise ValueError("Duplicate resume or job IDs prevent a safe dataset join.")

    resume_ids = set(resumes["resume_id"].astype(str))
    job_ids = set(jobs["job_id"].astype(str))
    if not set(matches["job_id"].astype(str)).issubset(job_ids):
        raise ValueError("Matches reference job IDs that are absent from the jobs table.")

    def text_list(value: object) -> list[str]:
        if value is None:
            return []
        if hasattr(value, "tolist"):
            value = value.tolist()
        if isinstance(value, (list, tuple)):
            return [str(item).strip() for item in value if str(item).strip()]
        return [str(value).strip()] if str(value).strip() else []

    resume_texts = resumes.copy()
    resume_texts["resume_text"] = resume_texts.apply(
        lambda row: "\n".join(
            part for part in [
                f"Role: {row['role']}",
                f"Seniority: {row['seniority']}",
                f"Experience: {row['years_experience']} years",
                f"Industry: {row['industry']}",
                f"Education: {row['education']}",
                "Skills: " + ", ".join(text_list(row["skills"])),
                str(row["summary"] or "").strip(),
                "Experience: " + "; ".join(text_list(row["experience_bullets"])),
            ] if part and not part.endswith(": ")
        ), axis=1
    )
    job_texts = jobs.copy()
    job_texts["job_description"] = job_texts.apply(
        lambda row: "\n".join(
            part for part in [
                f"Job title: {row['job_title']}",
                f"Seniority: {row['seniority']}",
                f"Industry: {row['industry']}",
                "Must-have skills: " + ", ".join(text_list(row["must_have_skills"])),
                "Preferred skills: " + ", ".join(text_list(row["nice_to_have_skills"])),
                str(row["description"] or "").strip(),
                "Responsibilities: " + "; ".join(text_list(row["responsibilities"])),
                "Requirements: " + "; ".join(text_list(row["requirements"])),
            ] if part and not part.endswith(": ")
        ), axis=1
    )

    rows: list[dict[str, str]] = []
    resume_lookup = resume_texts.set_index("resume_id")["resume_text"].to_dict()
    job_lookup = job_texts.set_index("job_id")["job_description"].to_dict()
    for match in matches.itertuples(index=False):
        job_id = str(match.job_id)
        relevant_ids = text_list(match.relevant_resume_ids)
        if len(relevant_ids) != len(set(relevant_ids)):
            raise ValueError(f"Duplicate relevant resume IDs for job {job_id}.")
        for resume_id in relevant_ids:
            if resume_id not in resume_ids:
                raise ValueError(f"Unknown resume ID {resume_id!r} for job {job_id}.")
            rows.append({
                "resume_id": resume_id,
                "job_id": job_id,
                "resume_text": resume_lookup[resume_id],
                "job_description": job_lookup[job_id],
                "match_label": "explicit_relevant",
                "label_source": "dataset relevant_resume_ids membership",
            })

    pairs = pd.DataFrame(rows)
    if pairs.empty or pairs.duplicated(["resume_id", "job_id"]).any():
        raise ValueError("Prepared positive pair data is empty or contains duplicate pairs.")
    return pairs


def write_positive_pairs(project_root: Path | None = None) -> Path:
    root = (project_root or find_project_root()).resolve()
    output = root / "data" / "processed" / "resume_job_positive_pairs.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    pairs = prepare_positive_pairs(root)
    pairs.to_csv(output, index=False)
    return output
