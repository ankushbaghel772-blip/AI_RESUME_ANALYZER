# Resume–job matching experiment data

The notebooks use the public `michaelozon/candidate-matching-synthetic` dataset:

<https://huggingface.co/datasets/michaelozon/candidate-matching-synthetic>

The Hugging Face dataset metadata currently declares the MIT license. The data are synthetic. The repository contains separate resume, job, and match tables. Its match table lists explicitly relevant resume IDs per job and caps the list at 30. It does not provide verified negative pairs or graded matching scores. The preparation code therefore emits only source-listed positive pairs; it never treats an unlisted pair as a negative.

The download helper checks that the dataset remains public, ungated, and declared MIT before downloading; it pins the resolved repository revision in `data/raw/dataset_manifest.json`. If the license or access status changes, download stops. Raw and processed data are reproducible outputs and are excluded from the final project ZIP.

These synthetic examples are for a controlled technical experiment. Similarity values from them are not human-validated matching performance or real-world hiring accuracy.
