1\. PARTY IDENTIFICATION RULES

1.1 Party Hierarchy



Every Sale Deed contains:



First Party



Seller(s)



Second Party



Buyer(s)



1.2 Source Priority



Party information should be extracted in the following order:



Priority 1



Identity Proof



Aadhaar

Driving Licence

Voter ID

Priority 2



PAN



Priority 3



Previous Deeds



Priority 4



Manual User Input



1.3 Name Mismatch Rule

Scenario



Aadhaar:



Ram Kishore



Sale Deed:



Ram Kishore Meena

Rule



Do not discard either name.



Generate:



Ram Kishore Meena @ Ram Kishore



Store:



{

&#x20; "name":"Ram Kishore Meena",

&#x20; "alias\_name":"Ram Kishore"

}

1.4 Relation Rule



Store:



पुत्र श्री मोहनलाल



as:



{

&#x20; "relation\_text":"पुत्र श्री मोहनलाल"

}



Do not separately store:



पुत्र

मोहनलाल



unless needed for legacy compatibility.



2\. PARTY TYPE DETECTION

2.1 Natural Person



Examples:



Akshat Sharma

Ram Kishore

Sunita Devi



Identity:



Aadhaar

DL

Voter ID

2.2 Proprietorship



Keywords:



Proprietor

Proprietorship

Owner

Sole Proprietor



Represented through:



Proprietor

POA Holder

2.3 Partnership Firm



Keywords:



Partnership

Partner

Partnership Firm



Represented through:



Partner

Authorized Signatory

POA Holder

2.4 Company



Keywords:



Private Limited

Ltd.

Limited

Pvt Ltd

LLP



Represented through:



Director

Authorized Signatory

POA Holder

2.5 Trust



Represented through:



Trustee

Authorized Signatory

POA Holder

2.6 HUF



Keywords:



HUF

Hindu Undivided Family



Represented through:



Karta



Store:



{

&#x20; "party\_type":"HUF",

&#x20; "representative":"Karta"

}

3\. MINOR RULES

3.1 Minor Buyer



Allowed.



Format:



Master X

through Natural Guardian

Y



Store:



{

&#x20; "is\_minor":true,

&#x20; "guardian\_name":"...",

&#x20; "guardian\_relation":"Father"

}

3.2 Minor Seller



High Risk.



Mandatory:



Court Permission



Validation:



ERROR:

Minor seller detected.

Court order required.

4\. PROPERTY DESCRIPTION RULES

4.1 Source Priority

Priority 1



Legal Search Report



Priority 2



Patta



Priority 3



Previous Sale Deed



Priority 4



ATS



Priority 5



Technical Report



5\. FLAT PROPERTY RULES



Mandatory Extraction:



Flat Number

Building Name

Floor Number



Optional:



Wing

Tower

Block

Area Type Detection



Capture:



Built-up Area

Super Built-up Area

Carpet Area



Store:



{

&#x20; "area\_type":"CARPET"

}

6\. PLOT / HOUSE RULES



Mandatory:



East-West Length



North-South Length



Total Area



Generate:



dimension\_text

7\. BOUNDARY RULES



Mandatory:



East

West

North

South



Store:



{

&#x20; "east":"...",

&#x20; "west":"...",

&#x20; "north":"...",

&#x20; "south":"..."

}

Road Validation



Check:



Road

Roadway

Rasta

Sadak

Marg



If none found:



WARNING:

No road boundary detected.

8\. PARKING RULES



Capture:



Parking Type



Reserved

Common

Car

Bike



Capture:



Parking Number



if available.



9\. PARTIAL PROPERTY RULES



Examples:



North Part

South Part

East Part

West Part

North-West Part



Store:



{

&#x20; "property\_portion":"NORTH\_PART"

}

10\. CHAIN ESTABLISHMENT RULES



Goal:



First Allottee

↓

Current Seller

Source Priority



1 TSR



2 Previous SD



3 Earlier Conveyance



Chain Validation



Check:



Seller Continuity



Seller of Deed N



must equal



Buyer of Deed N-1



Otherwise:



WARNING:

Chain discontinuity detected.

11\. CONSIDERATION RULES

Amount Source



Priority:



ATS



Else:



Banker Confirmation

Validation



SD Amount



must equal



ATS Amount



If mismatch:



ERROR:

Consideration mismatch.

12\. OCR RULES



OCR Total:



Sum of all payments



must be:



≤ Consideration Amount



If exceeded:



ERROR:

OCR exceeds consideration amount.

Account Rule



Capture:



Seller receiving account



not merely buyer paying account.



13\. TDS RULES



Trigger:



Consideration ≥ ₹50,00,000



Then:



TDS Applicable



Mandatory:



TDS Amount



TDS Challan



TDS Deposit Details



Validation:



WARNING:

Consideration exceeds ₹50 lakh but TDS details missing.

14\. REGISTRATION RULES



Map:



जिल्द संख्या

→ Volume Number

क्रम संख्या

→ Registration Serial Number

प्रतिफल राशि

→ Consideration Amount

15\. APP VALIDATION ENGINE

Errors



Block generation.



Examples:



Minor seller without court order



OCR > Consideration



Missing mandatory party

Warnings



Allow generation.



Examples:



No road boundary



Missing parking type



Chain mismatch

Info



Informational only.



Examples:



TDS applicable



Alias detected



Legal entity detected

FUTURE AI FEATURES



Automatically detect:



Alias names

Minor buyers

Minor sellers

HUFs

Companies

Trusts

Partnerships

OCR mismatches

Chain breaks

Missing road boundaries

Missing dimensions

Missing TDS

Parking inconsistencies

