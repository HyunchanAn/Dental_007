# FEA_for_Dentistry

![Status](https://img.shields.io/badge/Status-Under%20Construction-yellow) ![Python](https://img.shields.io/badge/Python-3.10%2B-blue)


## Technical Architecture & Workflow

### Architecture Diagram
```mermaid
graph TD
    A[Tooth STL Model] --> B[FEniCS Mesh Conversion]
    B --> C[Finite Element Analysis]
    C --> D[GLB Export & Visualization]
```
