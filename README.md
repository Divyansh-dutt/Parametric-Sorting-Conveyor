# Parametric-Sorting-Conveyor
Automated parametric conveyor framework for Autodesk Fusion 360 built with Python. Generates valid 3D CAD models with enforced design guardrails, revolute joint kinematics, physical material assignment, and real-time sorting simulations.


<div align="center">
  
#  Hyxon Parametric Sorting Conveyor Engine
**An API-driven CAD Generation & Kinematic Simulation Framework for Autodesk Fusion 360**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Autodesk Fusion 360](https://img.shields.io/badge/CAD-Autodesk%20Fusion%20360-blue.svg)](https://www.autodesk.com/products/fusion-360/)
[![Python 3.x](https://img.shields.io/badge/Language-Python%203.x-brightgreen.svg)](https://www.python.org/)
[![Status: Active](https://img.shields.io/badge/Status-Active-success.svg)]()

<p align="center">
  <img src="assets/generator_demo.gif" alt="Generator UI Demo" width="700"/>
</p>

</div>

---

## Table of Contents
- [Overview](#-overview)
- [System Architecture](#-system-architecture)
- [Key Features](#-key-features)
- [Installation Guide](#-installation-guide)
- [Usage Workflow](#-usage-workflow)
- [Engineering Constraints](#-engineering-constraints)
- [License](#-license)

---

##  Overview

Developed by **Team Hyxon**, this project completely automates the design, validation, and simulation of industrial sorting conveyors inside **Autodesk Fusion 360**. By leveraging Fusion's Python API, the framework eliminates manual 2D sketching and keyframe animation, replacing it with a fully parametric math-driven engine.

---

##  System Architecture

The framework operates via two synchronized Python scripts communicating through embedded document metadata (`root.attributes`):

1. **The Generator (`src/Mechanism_verifier.py`)**: Reads user input, computes exact mathematical 3D Boundary Representations (B-Rep), establishes As-Built Revolute Joints, and applies physical materials.
2. **The Physics Engine (`src/Animations.py`)**: Retrieves the metadata baked into the CAD file by the generator, computes the correct routing trajectory based on cargo weight, and drives real-time graphics rendering.

---

##  Key Features

* ** Zero-Sketch B-Rep Generation**: Mathematically computes components (frames, rollers, legs, guards) instantly.
* ** Constraint Validation**: Failsafes prevent generation of mechanically invalid designs.
* ** Automated Kinematics**: Auto-generates Revolute Joints for realistic physical motion.
* ** Smart Weight-Based Routing**: 
  * `Cargo > 10 kg` ➔ Routed **RIGHT**
  * `Cargo ≤ 10 kg` ➔ Routed **LEFT**
* ** Material Injection Engine**: Dynamically fetches Physical Materials (*Oak*, *Stainless Steel*, *ABS Plastic*) with guaranteed RGB custom appearance fallbacks.
* ** Live Analytics**: Built-in stopwatch generates a final logistics throughput report.

## 📁 Repository Structure

Hyxon-Parametric-Sorting-Conveyor/
│
├── src/                               # Source Code Directory
│   ├── Mechanism verifier.py          # Parametric CAD generator script
│   ├── Mechanism verifier.manifest    # Fusion 360 manifest file
│   ├── Animations.py                  # Simulation and sorting engine script
│   └── Animations.manifest            # Fusion 360 manifest file
│
├── .gitignore                         # Git configuration file
├── CONTRIBUTING.md                    # Open-source contribution guidelines
├── LICENSE                            # MIT License
└── README.md                          # Main project documentation

---

## Installation Guide

### Prerequisites
* **Autodesk Fusion 360** (Latest Version)
* Basic familiarity with the Fusion 360 Scripts & Add-Ins environment.

### Setup
1. Clone this repository:
   ```bash
   git clone [https://github.com/Divyansh-dutt/Hyxon-Parametric-Sorting-Conveyor.git](https://github.com/Divyansh-dutt/Hyxon-Parametric-Sorting-Conveyor.git)
