# Chrysus - Bank Statement Analysis & Loan Recommendation System

## Overview

Chrysus is an intelligent financial analysis platform that ingests bank statement PDFs, extracts and processes transaction data, and provides AI-powered loan recommendations. The system transforms unstructured bank documents into actionable insights for financial decision-making.

## Project Goals

The primary aim is to do an MVP showing how one could automate the labor-intensive process of analyzing bank statements for loan applications by:

1. **PDF Ingestion**: Extract tables and data from bank statement PDFs using OCR and text extraction
2. **Data Processing**: Transform raw data into structured, analyzable formats
3. **Feature Extraction**: Identify transaction patterns, categorize spending, and calculate financial metrics
4. **Intelligent Classification**: Use machine learning to categorize transactions and identify patterns
5. **Loan Recommendations**: Generate comprehensive loan recommendations with supporting evidence

## Architecture

### Backend (Python/FastAPI)

- **PDF Processing**: Uses `pdfplumber` for text extraction with `pytesseract` OCR fallback
- **LLM Integration**: Google Gemini 2.5 for table extraction and data processing
- **ML Classification**: Fine-tuned DeBERTa model for transaction categorization
- **Data Processing**: Pandas for data manipulation and feature engineering
- **API Layer**: FastAPI with CORS support for frontend communication

### Frontend (React/TypeScript)

- **Modern UI**: Built with React, TypeScript, and Tailwind CSS
- **Component Library**: Custom UI components with shadcn/ui
- **Data Visualization**: Recharts for financial charts and analytics
- **Responsive Design**: Mobile-friendly interface

## Implementation Details

### Data Extraction Pipeline

1. **PDF Text Extraction**:

   - Primary: `pdfplumber` for text extraction
   - Fallback: `pytesseract` OCR for image-based PDFs
   - Parallel processing for multiple tables

2. **LLM-Powered Table Extraction**:

   - Uses Gemini 2.5 to identify and extract tables from text
   - Structured XML prompts for consistent parsing
   - Automatic table description and categorization

3. **User Information Extraction**:
   - Extracts account holder name, account numbers, balances
   - Identifies account types and relevant financial metadata

### User Identification (Temporary Solution)

Since this is a POC without user management, the system uses a simple approach:

- **Name Extraction**: LLM extracts account holder names from PDFs
- **Account ID Linking**: Uses account numbers to link related statements
- **Limitation**: This approach works for data samples but isn't scalable for production

### Data Processing & Classification

1. **Transaction Classification**:

   - Fine-tuned DeBERTa model for initial categorization
   - LLM-based refinement for uncategorized transactions
   - Standardized categories: food, utilities, transportation, etc.

2. **Feature Engineering**:

   - Monthly/weekly spending patterns
   - Frequent transaction identification
   - Generalize statistics for the model to interpret

3. **Data Standardization**:
   - Unified date requirement with uniniform inputs
   - Standardized column names
   - Transaction amount normalization
   - inference where necessary

### Loan Recommendation System

The recommendation engine analyzes:

- **Base Insights**: High-level general statistics to find what to look for
- **Descriptive Tables**: Account summaries and additional financial data from the pdfs which don't link directly to transactions
- **Transaction History**: Detailed transaction records for evidence

Generates structured recommendations with:

- Clear decision (ACCEPT/REJECT/DEFER)
- Detailed reasoning
- Financial strengths and weaknesses
- Supporting evidence from transaction data

## Current Features

### ✅ Implemented

- PDF upload and processing - concurrent calls to make it less painful to wait - still slow can definitely be improved (split up tables - etc)
- Multi-table extraction from bank statements
- Transaction categorization and analysis
- Financial insights and statistics
- Interactive dashboard with multiple views
- Loan recommendation generation
- Responsive web interface

### 🔄 Partially Implemented

- Search functionality
- Export functionality (UI exists, not implemented)
- Filtering capabilities (UI exists, not implemented)
- Download button - UI exists couldn't decide how I wanted to put it together and doesn't matter for an MVP - was a waste of time to figure out do I want
  different files or not, etc.

### ❌ Not Implemented

- Advanced filtering and search
- Data export (CSV, PDF reports)
- User authentication and multi-user support
- Historical data comparison (if you were to give multiple pdfs of the same user though it would marry and you could do this)
- Uploading multiple pdfs at once. This one frustrated me enough in testing I almost just did it.

## Technical Challenges & Solutions

## Installation & Setup

### Prerequisites

- Python 3.10
- Node.js 18+
- PyTorch (install separately based on your system)

### Backend Setup

```bash
# Install PyTorch first (system-specific)
pip install torch torchvision torchaudio
# If you have a gpu do it via nvidia so you can use cuda & be faster - do the one for your driver ex i did:
# pip install --no-cache-dir torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1  --index-url https://download.pytorch.org/whl/cu126

# Install project dependencies
python -m pip install -e .

# Start the backend server
cd src/chrysus/backend
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd src/frontend
npm install
npm run dev
```

### Environment Variables

Create a `.env` file with:

```
GOOGLE_API_KEY=your_gemini_api_key
```

## Usage

1. **Upload PDF**: Use the file upload interface to add bank statements
2. **View Data**: Navigate between different views:
   - **Aggregate Stats**: High-level financial overview with charts
   - **Transactions**: Detailed transaction history with categorization
   - **Descriptive Tables**: Account summaries and additional data
   - **Recommendations**: AI-generated loan recommendations
3. **Analyze**: Review financial patterns, spending habits, and recommendations
   Once you have uploaded on you can play with the step 2/3 while it processes.

## Project Status: MVP/POC

This represents a bit more than one full day of focused development work hrs split over 2 days. While functional and demonstrating the core concept, several areas were left incomplete for speed. Architectures were rough for POC as well - the form I did for the core I would redesign. It is important to ideate more on what other features we would want to extract before deciding on a model. By having it this way, while it is clunky its incredibly malleable
