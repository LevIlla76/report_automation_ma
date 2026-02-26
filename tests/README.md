# Network Report Automation Gen 2

## Overview
A high-accuracy automation system for generating network infrastructure reports from screenshots and templates. Built with a focus on OCR precision and elegant user experience.

## Key Features
- **Geometric OCR Engine**: Advanced clustering and merging of text boxes to ensure decimal points and units (G, M, %) are captured correctly.
- **Image Preprocessing**: Neural-based upscaling (2.5x) and adaptive binarization to remove noise and watermarks.
- **Dynamic Slot Analysis**: Automatically identifies report requirements from Microsoft Word templates.
- **Premium UI**: Glassmorphic design with fluid animations and real-time status tracking.

## Tech Stack
### Backend (The Brain)
- **FastAPI**: Modern, high-performance web framework.
- **PaddleOCR (v4)**: State-of-the-art OCR model.
- **OpenCV**: Advanced image processing.
- **python-docx**: Document manipulation.

### Frontend (The Face)
- **React + Vite**: Fast and responsive UI.
- **Tailwind CSS**: Utility-first styling with custom dark theme.
- **Framer Motion**: Smooth micro-animations.
- **Lucide React**: Clean and professional iconography.

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+

### Installation

1. **Backend Setup**:
   ```bash
   cd backend
   pip install -r requirements.txt
   python ../run.py
   ```

2. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Validation
To run accuracy tests:
```bash
python -m tests.accuracy_test
```

## Project Structure
```text
network-report-gen2/
├── backend/            # Python FastAPI Service
│   ├── app/
│   │   ├── core/      # Logic (OCR, Preprocessor, Filler)
│   │   ├── api/       # Endpoints
│   │   └── schemas/   # Pydantic models
├── frontend/           # React Application
└── tests/              # Reliability & Accuracy Tests
```
