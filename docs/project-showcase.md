# Project Showcase

## One-Line Summary
Built an end-to-end IoT health monitoring system using ESP32 sensors, FastAPI, MySQL, Gemini AI, and a live web dashboard deployed through GitHub Pages.

## Problem
Remote health monitoring systems need a lightweight way to collect patient vitals, persist readings, and surface readable health summaries in near real time.

## Solution
This project uses an ESP32 with `MAX30102` and `DS18B20` sensors to capture SpO2, heart rate, and temperature, sends readings to a FastAPI backend, stores them in MySQL, generates structured AI assessments with Gemini, and displays the latest patient status on a responsive dashboard.

## Key Contributions
- Designed a modular FastAPI backend using route, service, and model separation
- Integrated SQLAlchemy with MySQL for persistent storage of readings and predictions
- Built live AI analysis using Gemini structured JSON output
- Developed a responsive frontend dashboard with auto-refresh polling
- Added ESP32 firmware for Wi-Fi connectivity and periodic sensor uploads
- Created a free demo deployment path using GitHub Pages and ngrok

## Resume Bullets
- Built an IoT health monitoring platform using ESP32, FastAPI, MySQL, and Gemini AI to collect, store, and interpret real-time patient vitals.
- Developed REST APIs for ingestion, latest status, and historical analytics with SQLAlchemy-based persistence and structured JSON responses.
- Implemented a responsive web dashboard and a GitHub Pages + ngrok demo deployment workflow for public project showcasing.
- Integrated embedded firmware with cloud-style backend services to stream sensor readings every 10 seconds over Wi-Fi.

