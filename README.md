# MCP_server_Firstlook(Anonymous Submission)

This repository contains the metadata and scripts used in our study *mcp-server-firstlook*, submitted for anonymous peer review.

The contents are organized according to the three research questions (RQ) explored in the paper.

---

## 📁 Dataset Metadata

The `metadata/` folder contains metadata used to support our analysis across RQ1–RQ3.

---

## 🔍 RQ1: Landscape 

- Folder: `RQ1-landscape/`

Contains scripts used to analyze the general landscape and distribution of MCP-servers.

---

## 💰 RQ2: Marketplace 

- Folder: `RQ2-marketplace/`

Includes scripts for exploring uniqueness, update behaviors, and vulnerabilities within the MCP server marketplace.

Subfolders:
- `uniqueness/res/`
- `update/`
- `vulnerability/`

---

## 🧰 RQ3: Tool Inconsistency Detection

- Folder: `RQ3-tool-inconsistency/`
- Key scripts:
  - `Python_Get_tool_DesSrc.py`: Extracts tools developed using the Python SDK from MCP-server metadata.
  - `Main_cot.py`: Detects and categorizes inconsistencies between tool descriptions and actual behavior.
  - `rule-based-filter.py`: Supporting script used for rule-based filtering in detection pipeline.

---

## 📝 Notes

- All scripts were used as part of a study-driven exploratory process.
- Each folder is self-contained and includes the scripts related to its respective question.
- Author-identifying information has been removed for double-blind review.
