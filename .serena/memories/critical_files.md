# Critical Files Memory

Below is a catalog of the primary files in the LegalDoc Automator repository:

## Core Web App
- **[app.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/app.py)**: Central Flask server. Defines REST routes, handles session saving/loading, serves HTML UI templates, and implements CORS & transliteration wrappers.

## Core Utilities
- **[utils/helpers.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/utils/helpers.py)**: Core normalization library. Implements `Unicode_to_KrutiDev`, relation splitting `parse_relation_text`, deceased prefix cleansers, currency formatters, and PDF hybrid page selectors. **DO NOT MODIFY WITHOUT CONSENT.**
- **[utils/devlys_to_unicode.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/utils/devlys_to_unicode.py)**: Translates legacy DevLys docx files back into clean Unicode Devanagari format.

## Registered Mortgage (RM) Module
- **[modules/rm/extractor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/rm/extractor.py)**: Gemini AI extraction wrappers for RM. Handles file ingestion, page pre-filtering, and API key rotations.
- **[modules/rm/processor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/rm/processor.py)**: Renders ICICI and other bank mortgage templates, applying Unicode-to-DevLys conversions.
- **[modules/rm/schema.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/rm/schema.py)**: Contains `prune_rm_data` serialization logic. Protects borrower/witness relation fields (`r` and `rn`).

## Sale Deed (SD) Module
- **[modules/sd/extractor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/extractor.py)**: Gemini AI extraction wrappers for SD documents.
- **[modules/sd/processor.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/processor.py)**: Renders sale deed templates and handles legacy DevLys detection (`is_text_devlys`).
- **[modules/sd/narrative.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/narrative.py)**: Narrative engine. Parses chain events and calls Gemini to write a formal Hindi property history block.
- **[modules/sd/schema.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/modules/sd/schema.py)**: Contains `prune_sd_data` serialization logic. Maps sellers/buyers list indices to maintain backend/frontend parity.

## Template Builder System
- **[template_tools/template_builder.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/template_tools/template_builder.py)**: Tkinter desktop interface to map fields to Jinja tags.
- **[template_tools/builder_core.py](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/template_tools/builder_core.py)**: Contains replacement engines and standard field specifications (`RM_FIELDS`, `SD_FIELDS`).

## e-Panjiyan Autofill Extensions
- **[extensions/epanjiyan_autofill/content.js](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/extensions/epanjiyan_autofill/content.js)**: Injected JS script to automate the portal flow for RM deeds.
- **[extensions/epanjiyan_sd_autofill/content.js](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/extensions/epanjiyan_sd_autofill/content.js)**: Injected JS script to automate the portal flow for SD deeds.
