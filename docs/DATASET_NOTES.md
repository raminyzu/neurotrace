# CHB-MIT Dataset Notes

## 1. Dataset Source

- Name: CHB-MIT Scalp EEG Database
- Provider: PhysioNet
- Version: 1.0.0
- URL: https://physionet.org/content/chbmit/1.0.0/
- License: Open Data Commons Attribution License v1.0

## 2. Dataset Characteristics

- 22 individuals represented across 23 original recording cases, with chb24 also included.
- 686 EDF recordings, verified against the official RECORDS index.
- Approximately 42.6 GB of downloaded data.
- Sampling frequency: 256 Hz.
- Typical number of EEG channels: 23.
- Signal resolution: 16-bit.
- 198 seizure events reported for the dataset.

### Local Download Verification

The complete dataset download was checked against the official RECORDS index.

| Verification | Result |
|---|---:|
| EDF files listed in RECORDS | 686 |
| EDF files present locally | 686 |
| Missing EDF files | 0 |
| Extra EDF files | 0 |

## 3. Important Files

| File type | Purpose |
|---|---|
| .edf | EEG signal recordings |
| -summary.txt | Recording information and seizure timings |
| .edf.seizures | Seizure event annotation files |
| RECORDS | List of available EDF recordings |
| RECORDS-WITH-SEIZURES | Index of recordings identified as containing seizures |
| SUBJECT-INFO | Subject information |

## 4. Research Considerations

- Preserve patient identity when preparing datasets.
- Avoid patient overlap between training and testing.
- Account for recordings with different durations.
- Inspect channel names and sampling frequencies.
- Verify seizure annotations before generating labels.
- Keep raw recordings unchanged.
- Do not rely exclusively on RECORDS-WITH-SEIZURES when identifying seizure recordings; cross-check the summary and annotation files.

## 5. Known Dataset Limitations and Observations

### 5.1 Patient Identity

Cases chb01 and chb21 belong to the same individual. They must be treated as one individual when designing patient-independent data splits.

### 5.2 CHB07 Metadata Inconsistency

An inconsistency was identified during local dataset inspection:

- RECORDS-WITH-SEIZURES lists chb07/chb07_18.edf.
- chb07-summary.txt reports zero seizures in chb07_18.edf.
- The same summary reports one seizure in chb07_19.edf, starting at 13,688 seconds and ending at 13,831 seconds.
- The corresponding chb07_19.edf.seizures annotation sidecar exists, while a matching sidecar for chb07_18.edf was not found.

This discrepancy is documented for research transparency. Original dataset files have not been modified. Seizure labels must be verified against the relevant recording summary and annotation data.

## 6. Research Integrity

NeuroTrace is an experimental research project.
Its outputs are not clinically validated and must not be
used for medical diagnosis or treatment decisions.

## 7. Reference

Guttag, J. (2010). CHB-MIT Scalp EEG Database (version 1.0.0).
PhysioNet. https://doi.org/10.13026/C2K01R

