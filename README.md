**NormalControllerBot: Telegram Bot for Technical Specification Review**

Overview

This project implements a Telegram bot designed to review technical specifications (рг) for compliance with Russian GOST standards and best practices. The bot accepts text messages or files (PDF) containing technical specifications, analyzes them using a language model (via g4f), and provides detailed feedback on errors, inconsistencies, and suggestions for improvement. The analysis focuses on the structure, content, formatting, and clarity of the specification, with a specific emphasis on battery development for electric vehicles.

Features

* Telegram Integration: Interacts with users via Telegram, handling text messages and file uploads (PDF).

* Technical Specification Analysis: Checks compliance with GOST standards (e.g., GOST 15.016-2016, GOST R 53778-2010) and other relevant norms.

* Language Model Integration: Uses g4f (default: gpt-4.1-mini) for analyzing specifications and generating detailed feedback.

* File Processing: Extracts text from PDF files for analysis.

* PDF Output: Generates PDF reports for long analysis results using ReportLab.

* Error Handling: Robust handling of invalid inputs, large files, and processing errors.

* Asynchronous Processing: Utilizes asyncio for efficient handling of Telegram updates and LLM requests.

* Configurable: Supports customizable settings for LLM model, timeouts, retry attempts, and file size limits.

Requirements

To run this project, install the following Python packages:
pip install python-telegram-bot g4f PyPDF2 reportlab

Additional requirements:

* Times New Roman font files (times.ttf, timesbd.ttf) for PDF generation, placed in the project directory.

* Telegram Bot Token: Obtain from @BotFather on Telegram and set as TELEGRAM_BOT_TOKEN environment variable.

* Optional: Internet access for g4f to interact with the language model.

Configuration

The bot uses a CONFIG dictionary to manage settings:

* llm_model: Language model to use (default: gpt-4.1-mini).

* retry_attempts: Number of retries for LLM requests (default: 3).

* retry_interval: Seconds between retries (default: 5).

* llm_timeout: Timeout for LLM requests (default: 120 seconds).

* max_file_size: Maximum file size for uploads (default: 20 MB).

* telegram_timeout: Timeout for Telegram API requests (default: 60 seconds).

* max_message_length: Maximum length for Telegram text replies (default: 4000 characters).

Usage

Set up the Telegram bot token:

* Obtain a token from @BotFather.

* Set it as an environment variable: export TELEGRAM_BOT_TOKEN="your_token_here"

* Place Times New Roman font files (times.ttf, timesbd.ttf) in the project directory.

* Run the bot: python normal_controller_bot.py

Interact with the bot:

* Send /start to receive a welcome message.

* Send text containing a technical specification or upload a PDF file.

* The bot will analyze the specification and reply with feedback or a PDF report for long responses.

Code Structure

* NormalControllerBot: Main class handling Telegram bot setup, message/file processing, and LLM analysis.

* initialize(): Initializes and starts the Telegram application.

* setup_handlers(): Registers handlers for /start, text messages, and document uploads.

* start(): Sends a welcome message.

* handle_text(): Processes text-based specifications.

* handle_document(): Processes uploaded PDF files.

* extract_text_from_file(): Extracts text from PDF files.

* analyze_tz(): Sends the specification to the LLM for analysis.

* _llm_request(): Handles LLM requests with retries and timeouts.

* send_analysis(): Sends analysis results as text or PDF.

* create_pdf(): Generates PDF reports using ReportLab.

* main_handler(): Lambda-compatible handler for processing Telegram updates (e.g., in AWS Lambda).

Technical Specification Analysis

The bot analyzes technical specifications for compliance with standards like:

* GOST 15.016-2016 (System of Product Development and Launch)

* GOST R 53778-2010 (Battery General Technical Conditions)

* GOST R 52350.11-2005 (Battery Safety Requirements)

* GOST 12.2.007.0-75 (Electrical Safety)

* GOST 30804.4.2-2013, GOST 30804.4.3-2013 (Electromagnetic Compatibility)

* GOST 12.1.044-89 (Fire Safety)

* PUE (Electrical Installation Rules)

* NPB 105-03 (Fire Safety Norms for Battery Rooms)

* ISO 12405, IEC 62660 (International battery standards)

The analysis checks:

* Structure: Presence of required sections (e.g., Introduction, Technical Requirements, Safety).

* Content: Specific, measurable, achievable, relevant, and time-bound (SMART) requirements, including battery parameters (voltage, capacity, type, etc.).

* Formatting: Proper fonts, margins, numbering, and references.

* Clarity: Clear, concise language with defined technical terms.

* Battery-Specific Checks: Capacity optimization, temperature resilience, vibration/mechanical durability, and compliance with modern battery technologies.

Output Format

The analysis follows a structured format for each issue:

* Was: [Quote or description of the issue]

* Remark: [Explanation of the issue, referencing standards or best practices]

* Should Be: [Proposed correction]

For example:

* Was: The document lacks a "Documentation Requirements" section.

* Remark: GOST 15.016-2016 mandates a section on required documentation formats.

* Should Be: Add a "Documentation Requirements" section listing necessary documents per GOST R 15.301.

Notes

* The bot assumes PDF files are text-readable. Scanned PDFs may require OCR (not supported).

* Large analysis results are sent as PDFs to comply with Telegram's message length limits.

* The bot uses Times New Roman fonts for PDF generation to match standard documentation formatting.

* Ensure the g4f library is configured to access a compatible language model.

* The main_handler function is designed for serverless deployment (e.g., AWS Lambda) but can be adapted for local execution.

License

This project is licensed under the MIT License.
