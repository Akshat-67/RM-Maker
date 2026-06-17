# Title Chain Event Library (`CHAIN_EVENT_LIBRARY.md`)

This library documents the specific extraction requirements and template rendering patterns for each canonical Title Chain event type based on real-world DevLys Sale Deeds.

---

## 1. ALLOTMENT (आवंटन पत्र / पट्टा विलेख)

**Description:** The root document of a title chain, typically issued by a housing society, development authority (e.g., JDA), or government body.

**Extraction Fields:**
- `document_name`: "पट्टा विलेख" or "आवंटन पत्र"
- `executant.name`: Name of Authority (e.g., "जयपुर विकास प्राधिकरण")
- `claimant.name`: Original Allottee
- `registration`: Details of the registered lease/patta.

**Hindi Rendering Variables (Jinja2 equivalent):**
- `{{tc.document_name}}`
- `{{tc.executant.name}}`
- `{{tc.claimant.name}}`

**Sample DevLys Text (from actual deeds):**
> "...जयपुर विकास प्राधिकरण, जयपुर ने पट्टा विलेख आवंटन/विक्रय-पत्र संख्या डी-2341 दिनांक 17-04-2018 ईस्वी को श्रीमती राजबाला... के हित में निष्पादित कर जारी कर दिया..."

**Sample Hindi Deed Language:**
> "यह कि उक्त वर्णित संपत्ति का मूल **{{tc.document_name}}** **{{tc.executant.name}}** द्वारा **{{tc.claimant.name}}** के पक्ष में दिनांक **{{tc.date}}** को जारी किया गया, जो उप-पंजीयक **{{tc.registration.office}}** के कार्यालय में दिनांक **{{tc.registration.date}}** को पुस्तक संख्या **{{tc.registration.book}}**, जिल्द संख्या **{{tc.registration.vol}}** में पृष्ठ संख्या **{{tc.registration.page}}** क्रम संख्या **{{tc.registration.reg_no}}** पर पजीबद्ध किया गया तथा अतिरिक्त पुस्तक संख्या **{{tc.registration.add_book}}** जिल्द संख्या **{{tc.registration.add_vol}}** के पृष्ठ संख्या **{{tc.registration.add_page}}** पर चस्पा किया गया।"

---

## 2. SALE_DEED (विक्रय पत्र / बेचाननामा)

**Description:** A standard transfer of ownership for monetary consideration.

**Extraction Fields:**
- `document_name`: "विक्रय पत्र"
- `executant`: Seller details
- `claimant`: Buyer details
- `consideration_amount`: Amount (not strictly required for the chain narrative, but good for context).
- `registration`: Mandatory.

**Sample DevLys Text (from actual deeds):**
> "तत्पश्चात श्रीमती राजबाला... ने उक्त मूल सम्पत्ति को जरिये पंजीकृत विक्रय पत्र दिनांकित 23-04-2018 द्वारा मैसर्स स्नेहा बिल्डिंग मैटेरियल सप्लायर्स... को विक्रय कर दिया..."

**Sample Hindi Deed Language:**
> "तत्पश्चात **{{tc.executant.name}}** ने उक्त संपत्ति को जरिये पंजीकृत **{{tc.document_name}}** दिनांक **{{tc.date}}** द्वारा **{{tc.claimant.name}}** को विक्रय कर दिया, जिसका पंजीयन उप-पंजीयक कार्यालय **{{tc.registration.office}}** के यहाँ दिनांक **{{tc.registration.date}}** को पुस्तक संख्या **{{tc.registration.book}}** जिल्द संख्या **{{tc.registration.vol}}** में पृष्ठ संख्या **{{tc.registration.page}}** क्रम संख्या **{{tc.registration.reg_no}}** पर पजीबद्ध किया गया तथा अतिरिक्त पुस्तक संख्या **{{tc.registration.add_book}}** जिल्द संख्या **{{tc.registration.add_vol}}** के पृष्ठ संख्या **{{tc.registration.add_page}}** पर चस्पा किया गया।"

---

## 3. POA (मुख्तियारनामा आम / खास)

**Description:** Power of Attorney granting authority to sell or manage the property.

**Extraction Fields:**
- `document_name`: "मुख्तियारनामा आम" (GPA)
- `executant`: Principal (Owner)
- `claimant`: Attorney (Agent)

**Sample Hindi Deed Language:**
> "तदुपरांत **{{tc.executant.name}}** ने अपने पक्ष में **{{tc.claimant.name}}** को एक पंजीकृत **{{tc.document_name}}** दिनांक **{{tc.date}}** को निष्पादित किया, जिसके आधार पर उन्हें संपत्ति के बेचान का पूर्ण अधिकार प्राप्त हुआ। जिसका पंजीयन..." (Registration details follow standard format).

---

## 4. RELINQUISHMENT (हकत्याग पत्र)

**Description:** Surrender of rights by one or more co-owners.

**Extraction Fields:**
- `document_name`: "हकत्याग पत्र"

**Sample Hindi Deed Language:**
> "तदुपरांत **{{tc.executant.name}}** ने अपना संपूर्ण हिस्सा एवं अधिकार **{{tc.claimant.name}}** के पक्ष में बिना किसी प्रतिफल के त्यागते हुए एक **{{tc.document_name}}** दिनांक **{{tc.date}}** को निष्पादित एवं पंजीकृत करवाया।" (Registration details follow standard format).
