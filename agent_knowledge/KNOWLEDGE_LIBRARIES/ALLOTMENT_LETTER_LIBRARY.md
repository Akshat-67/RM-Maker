# Allotment Letter Library

**Path:** `agent_knowledge/KNOWLEDGE_LIBRARIES/ALLOTMENT_LETTER_LIBRARY.md`

This document details the usage, patterns, and structure of Allotment Letters (आवंटन पत्र / vkoaVu i=) as found in the firm's historical knowledge corpus of Sale Deeds. It serves as institutional memory to inform future automated extraction, schema development, and document generation.

---

## 1. Corpus Findings

An analysis of approximately 60 historical sale deeds (and related documents) was performed. 
- Over **58 files** explicitly reference allotment letters in their title chains.
- Allotment letters serve as the foundational, root-of-title document for nearly all society-issued and JDA-issued plots.
- The phrase "सर्वप्रथम" (firstly/initially) almost exclusively precedes the mention of an allotment letter, signifying it as the first event in the property's recorded title chain.
- Allotment letters are intimately tied to receipts ("रसीद संख्या"), site plans ("साइट प्लान"), and possession ("कब्जा"). If a party is allotted a plot, they must pay a specific sum (evidenced by a receipt), after which they receive the allotment letter, the site plan, and physical possession.

---

## 2. Authority Taxonomy

The corpus reveals three primary categories of authorities that issue allotment letters:

### A. Cooperative Housing Societies (गृह निर्माण सहकारी समिति / को-ओपरेटिव हाउसिंग सोसायटी)
The vast majority of allotments in the corpus were issued by housing societies. 
*Examples:*
- हरिनगर गृह निर्माण सहकारी समिति लि. (Harinagar Grih Nirman Sahkari Samiti Ltd.)
- राजहंस गृह निर्माण सहकारी समिति लि. (Rajhans Grih Nirman Sahkari Samiti Ltd.)
- वाटिका गृह निर्माण सहकारी समिति लिमिटेड (Vatika Grih Nirman Sahkari Samiti Ltd.)
- लक्ष्मी नगर गृह निर्माण सहकारी समिति लि0 (Laxmi Nagar Grih Nirman Sahkari Samiti Ltd.)

### B. Jaipur Development Authority (JDA / जयपुर विकास प्राधिकरण)
JDA issues allotment letters or regularizes society plots. In many cases, JDA does not issue the *first* allotment, but rather regularizes a society allotment by taking payment and issuing a "पट्टा विलेख" (Lease Deed) based on a prior possession letter / allotment letter. However, some plots are directly allotted by JDA.

### C. Rajasthan Housing Board (RHB / राजस्थान आवासन मण्डल)
RHB issues an "Allotment cum Possession Letter" (आवंटन कम पजेशन पत्र). These are often followed by an "अदेय प्रमाण पत्र" (No Dues Certificate) and a "लीज मनी प्रमाण पत्र" (Lease Money Certificate).

---

## 3. Allotment Number Patterns

### A. Society Allotments
Most society allotment letters in the corpus **do not list a discrete allotment letter number**. Instead, the society's legitimacy is established via its **Registration Number** (पंजीयन क्रमांक).
*Pattern:*
`पंजीयन क्रमंाक <Number>/एल.`
*Examples:*
- 2724/एल.
- 59/एल.आर.
- 2493/एल.
- 2632/एल

The unique identifier for a society transaction is typically the **Receipt Number** (रसीद संख्या) for the money paid at the time of allotment, rather than an allotment letter number.
*Examples of Receipt Numbers:*
- 13538
- एच-62031 (H-62031)
- 50618
- ए-5390 (A-5390)

### B. JDA / RHB Allotments
Government body allotments generally feature explicit, complex file/dispatch numbers.
*JDA Pattern Example:*
`एफ-9 (डी/295) जेडीए/ सी-1/ पी/ गोविन्दपुरा /97/ डी` (F-9 (D/295) JDA/ C-1/ P/ Govindpura /97/ D)
*RHB Pattern Example:*
`2098` (Numeric dispatched number)

---

## 4. Common Legal Language

The language surrounding the allotment event is highly standardized across the corpus.

**1. The Root Event (The Allotment)**
*Original (KrutiDev)*: ;g fd loZizFke mDr lEifRr...
*Hindi (Unicode)*: यह कि सर्वप्रथम उक्त सम्पत्ति [Authority Name] द्वारा [Allottee Name] को जरिये आवंटन पत्र आवंटित किया गया था...
*English*: That firstly, the said property was allotted by [Authority Name] to [Allottee Name] via Allotment Letter...
*Explanation*: Establishes the origin of the title.

**2. The Financial Consideration**
*Hindi (Unicode)*: ...तथा उक्त सम्पत्ति की मांगी गई समस्त राशियाँ [Allottee Name] ने जरिये रसीद संख्या [Receipt No] दिनांक [Date] को जमा करवा कर...
*English*: ...and all demanded amounts for the said property were deposited by [Allottee Name] via Receipt No. [Receipt No] dated [Date]...
*Explanation*: Proves that the allottee paid the required society dues.

**3. Possession and Site Plan**
*Hindi (Unicode)*: ...उक्त सम्पत्ति का कब्जा वास्तविक मौके पर मय साइट प्लान के साथ प्राप्त कर लिया।
*English*: ...obtained actual physical possession of the said property on site along with the site plan.
*Explanation*: "कब्जा" (possession) and "साइट प्लान" (site plan) are legally coupled with the allotment. Without possession, the allotment is incomplete.

**4. Vesting of Absolute Rights**
*Hindi (Unicode)*: इस प्रकार [Allottee Name] उक्त सम्पत्ति का एकमात्र स्वामी, मालिक एवं काबिज हुआ।
*English*: Thus, [Allottee Name] became the sole owner, proprietor, and possessor of the said property.

---

## 5. Typical Title-Chain Usage

The Allotment Letter is the Step 1 node in a linear title chain. 

**Standard Chain:**
1. **Allotment** (आवंटन) -> 
2. **Transfer via Agreement/Will** (तत्पश्चात... हस्तान्तरण) -> 
3. **Regularization/Lease Deed by JDA** (पट्टा विलेख) -> 
4. **Current Sale Deed** (विक्रय पत्र)

When a property is transferred *before* a formal JDA Lease Deed is issued, the title chain text will use words like **तत्पश्चात** (Thereafter):
*Hindi (Unicode)*: तत्पश्चात [New Buyer] ने उक्त वणित सम्पति को [Original Allottee] से क्रय कर नियमानुसार समिति द्वारा चाही गई समुचित राशियां जरिये रसीद संख्या [New Receipt] जमा करवाकर कब्जा प्लाट व समस्त असल दस्तावेज आवंटन पत्र मय साईट प्लान, रसीद समिति से अपने नाम हस्तान्तरण करवाकर प्राप्त कर लिये।
*English*: Thereafter, [New Buyer] purchased the said property from [Original Allottee] and deposited the required amounts in the society... getting the original documents, allotment letter, site plan, and receipt transferred to their name.

This demonstrates that "Allotment Letters" are physically handed over from seller to buyer as the primary proof of title until a formal Lease Deed is generated by the government.

---

## 6. Edge Cases

1. **Missing Allotment Numbers:** As noted, society allotments almost never have a discrete "Allotment Number". The system must not force/require an `allotment_number` field if the authority is a cooperative society. The `receipt_number` acts as the transaction identifier.
2. **"Allotment cum Possession" Letters:** Rajasthan Housing Board combines these into a single document ("आवंटन कम पजेशन पत्र").
3. **Corporate Entities as Allottees:** Sometimes the allottee is not an individual, but a builder/firm (e.g., मैसर्स साक्षी बिल्डर्स प्रोपराईटर श्रीमती वैशाली गर्ग - M/s Shakshi Builders proprietor Smt. Vaishali Garg).
4. **Name Transfers within Societies:** If Person A sells to Person B, the society might issue a *new* allotment letter or simply endorse the transfer. The drafting language lumps this together as "हस्तान्तरण करवाकर प्राप्त कर लिये" (transferred and obtained).

---

## 7. Recommended Structured Schema

Based on the evidence, an allotment schema must capture the authority, the payment proof, and the possession status.

**Field Descriptions:**
- `authority_name` (String): The name of the society, board, or authority issuing the allotment (e.g., "हरिनगर गृह निर्माण सहकारी समिति लि.").
- `authority_registration_number` (String, Optional): The registration number of the society (e.g., "2724/एल.").
- `allottee_name` (String): The person or entity to whom the property was allotted.
- `allotment_number` (String, Optional): The formal dispatch number of the letter (common for JDA/RHB, rare for societies).
- `allotment_date` (String): The date of the allotment letter.
- `receipt_number` (String, Optional): The receipt number for the payment made against the allotment (highly common for societies).
- `receipt_date` (String, Optional): The date the payment was made.
- `site_plan_included` (Boolean): Whether the site plan (साइट प्लान) was handed over.
- `possession_handed_over` (Boolean): Whether physical possession (कब्जा) was given.

**JSON Schema Example:**
```json
{
  "allotment_event": {
    "authority_name": "हरिनगर गृह निर्माण सहकारी समिति लि.",
    "authority_registration_number": "2724/एल.",
    "allottee_name": "श्रीमती कमली देवी पत्नी श्री भगवान सहाय",
    "allotment_number": null,
    "allotment_date": "21.06.2013",
    "receipt_number": "9606",
    "receipt_date": "21.06.2013",
    "site_plan_included": true,
    "possession_handed_over": true
  }
}
```

---

## 8. Examples from Real Deeds

**Example 1: Standard Society Allotment**
*Hindi (Unicode)*:
यह कि सर्वप्रथम उक्त सम्पत्ति हरिनगर गृह निर्माण सहकारी समिति लिमिटेड जयपुर, पंजीयन क्रमंाक 2724/एल द्वारा साक्षी बिल्डर्स प्रोपराईटर श्रीमती वैशाली गर्ग को जरिये आवंटन पत्र आवंटित किया गया था तथा उक्त सम्पत्ति की मांगी गई समस्त राशियाँ साक्षी बिल्डर्स ने जरिये रसीद संख्या एच-62031 दिनांकित 24.12.2025 को जमा करवा कर उक्त सम्पत्ति का कब्जा वास्तविक मौके पर मय साइट प्लान के साथ प्राप्त कर लिया।
*English Explanation*:
Demonstrates the standard society allotment. Note the Registration Number "2724/एल", the lack of an allotment letter number, the presence of a receipt "एच-62031", and the explicit mention of physical possession and site plan.

**Example 2: Transfer of Society Allotment Rights**
*Hindi (Unicode)*:
तत्पश्चात श्री विकास मीणा पुत्र श्री दिनेश मीणा ने प्लाट न. 21... को श्रीमती कमली देवी से क्रय कर नियमानुसार समिति द्वारा चाही गई समस्त मांग राशि जरिये रसीद संख्या एच-59909 दिनांक 11.08.2025 के द्वारा समिति में जमा करवाकर कब्जा प्लाट व समस्त असल दस्तावेज आवंटन पत्र मय साईट प्लान... अपने नाम हस्तान्तरण करवाकर प्राप्त कर लिए।
*English Explanation*:
Demonstrates how title passes before a formal JDA lease is created. The buyer pays a transfer fee to the society (evidenced by a new receipt) and takes physical custody of the original allotment letter and site plan.

**Example 3: JDA Allotment**
*Hindi (Unicode)*:
...श्री राकेश यादव पुत्र श्री रामगोपाल यादव को कार्यालय जयपुर विकास प्राधिकरण जयपुर के आवंटन पत्र कमांक एफ-9 (डी/295) जेडीए/ सी-1/ पी/ गोविन्दपुरा /97/ डी दिनांक 04.06.1997 को आवंटित किया गया...
*English Explanation*:
Demonstrates a JDA allotment. Unlike a society, JDA issues a highly specific file dispatch number.

---

## 9. Future System Support Recommendations

1. **Do not strictly require `allotment_number`**: Extraction AI and Schema Validation must treat `allotment_number` as optional. If the authority contains "समिति" (Society), the AI should look for a `receipt_number` (रसीद संख्या) instead.
2. **Coupled Events**: The system should recognize that "Allotment", "Payment of Fees", "Receipt of Site Plan", and "Taking Possession" are functionally treated as a single compound event in the legal drafting. 
3. **Society Registration Extractions**: When extracting the authority name, the AI should be trained to separate the Registration Number (e.g., "पंजीयन क्रमंाक 2724/एल") from the Society Name string, as drafters frequently concatenate them in the source text.
4. **Original Document Custody**: The extraction schema might benefit from a `documents_transferred` array to capture when a title transition involves handing over the "असल दस्तावेज आवंटन पत्र मय साईट प्लान" (Original documents, allotment letter, and site plan).
