"""Seed medical coding tables with common cardiology codes.

Usage:
    cd backend
    python -m scripts.seed_codes

Seeds ICD-10 (cardiac chapters I20-I52), CPT (echo, ECG, cath, PCI),
HIO service codes, ATC (cardiac drugs), LOINC (cardiac labs),
and Gesy medications (common cardiology pharmaceuticals).
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory, engine


# =============================================================================
# ICD-10 Cardiac Diagnosis Codes (I20-I52)
# =============================================================================
ICD10_CODES = [
    # Ischemic heart disease (I20-I25)
    ("I20.0", "Unstable angina", "Ασταθής στηθάγχη", "I", "Ischemic heart disease"),
    ("I20.1", "Angina pectoris with documented spasm", "Στηθάγχη με τεκμηριωμένο σπασμό", "I", "Ischemic heart disease"),
    ("I20.8", "Other forms of angina pectoris", "Άλλες μορφές στηθάγχης", "I", "Ischemic heart disease"),
    ("I20.9", "Angina pectoris, unspecified", "Στηθάγχη, μη καθορισμένη", "I", "Ischemic heart disease"),
    ("I21.0", "Acute ST elevation MI of anterior wall", "Οξύ STEMI πρόσθιου τοιχώματος", "I", "Acute MI"),
    ("I21.1", "Acute ST elevation MI of inferior wall", "Οξύ STEMI κατώτερου τοιχώματος", "I", "Acute MI"),
    ("I21.2", "Acute ST elevation MI of other sites", "Οξύ STEMI άλλων εντοπίσεων", "I", "Acute MI"),
    ("I21.3", "Acute ST elevation MI of unspecified site", "Οξύ STEMI μη καθορισμένης εντόπισης", "I", "Acute MI"),
    ("I21.4", "Acute subendocardial MI (NSTEMI)", "Οξύ υπενδοκάρδιο ΕΜ (NSTEMI)", "I", "Acute MI"),
    ("I21.9", "Acute myocardial infarction, unspecified", "Οξύ έμφραγμα μυοκαρδίου, μη καθορισμένο", "I", "Acute MI"),
    ("I22.0", "Subsequent MI of anterior wall", "Υποτροπιάζον ΕΜ πρόσθιου τοιχώματος", "I", "Subsequent MI"),
    ("I22.1", "Subsequent MI of inferior wall", "Υποτροπιάζον ΕΜ κατώτερου τοιχώματος", "I", "Subsequent MI"),
    ("I25.1", "Atherosclerotic heart disease", "Αθηροσκληρωτική καρδιοπάθεια", "I", "Chronic ischemic"),
    ("I25.2", "Old myocardial infarction", "Παλαιό έμφραγμα μυοκαρδίου", "I", "Chronic ischemic"),
    ("I25.5", "Ischemic cardiomyopathy", "Ισχαιμική μυοκαρδιοπάθεια", "I", "Chronic ischemic"),
    ("I25.10", "Coronary artery disease (native vessel)", "Στεφανιαία νόσος (αυτόχθονο αγγείο)", "I", "Chronic ischemic"),
    # Pulmonary heart disease (I26-I28)
    ("I26.0", "Pulmonary embolism with acute cor pulmonale", "Πνευμονική εμβολή με οξεία πνευμονική καρδία", "I", "Pulmonary heart"),
    ("I26.9", "Pulmonary embolism without acute cor pulmonale", "Πνευμονική εμβολή χωρίς οξεία πνευμονική καρδία", "I", "Pulmonary heart"),
    ("I27.0", "Primary pulmonary hypertension", "Πρωτοπαθής πνευμονική υπέρταση", "I", "Pulmonary heart"),
    ("I27.2", "Other secondary pulmonary hypertension", "Άλλη δευτεροπαθής πνευμονική υπέρταση", "I", "Pulmonary heart"),
    # Other heart diseases (I30-I52)
    ("I30.9", "Acute pericarditis, unspecified", "Οξεία περικαρδίτιδα, μη καθορισμένη", "I", "Pericardial"),
    ("I31.3", "Pericardial effusion (noninflammatory)", "Περικαρδιακή συλλογή (μη φλεγμονώδης)", "I", "Pericardial"),
    ("I33.0", "Acute and subacute infective endocarditis", "Οξεία λοιμώδης ενδοκαρδίτιδα", "I", "Endocarditis"),
    ("I34.0", "Nonrheumatic mitral valve insufficiency", "Μη ρευματική ανεπάρκεια μιτροειδούς", "I", "Valvular"),
    ("I34.1", "Nonrheumatic mitral valve prolapse", "Μη ρευματική πρόπτωση μιτροειδούς", "I", "Valvular"),
    ("I35.0", "Nonrheumatic aortic valve stenosis", "Μη ρευματική στένωση αορτικής βαλβίδας", "I", "Valvular"),
    ("I35.1", "Nonrheumatic aortic valve insufficiency", "Μη ρευματική ανεπάρκεια αορτικής βαλβίδας", "I", "Valvular"),
    ("I35.2", "Nonrheumatic aortic stenosis with insufficiency", "Μη ρευματική στένωση αορτής με ανεπάρκεια", "I", "Valvular"),
    ("I42.0", "Dilated cardiomyopathy", "Διατατική μυοκαρδιοπάθεια", "I", "Cardiomyopathy"),
    ("I42.1", "Obstructive hypertrophic cardiomyopathy", "Αποφρακτική υπερτροφική μυοκαρδιοπάθεια", "I", "Cardiomyopathy"),
    ("I42.2", "Other hypertrophic cardiomyopathy", "Άλλη υπερτροφική μυοκαρδιοπάθεια", "I", "Cardiomyopathy"),
    ("I44.0", "First degree atrioventricular block", "Κολποκοιλιακός αποκλεισμός πρώτου βαθμού", "I", "Conduction"),
    ("I44.1", "Second degree atrioventricular block", "Κολποκοιλιακός αποκλεισμός δευτέρου βαθμού", "I", "Conduction"),
    ("I44.2", "Complete atrioventricular block", "Πλήρης κολποκοιλιακός αποκλεισμός", "I", "Conduction"),
    ("I45.10", "Right bundle-branch block", "Αποκλεισμός δεξιού σκέλους", "I", "Conduction"),
    ("I47.1", "Supraventricular tachycardia", "Υπερκοιλιακή ταχυκαρδία", "I", "Arrhythmia"),
    ("I47.2", "Ventricular tachycardia", "Κοιλιακή ταχυκαρδία", "I", "Arrhythmia"),
    ("I48.0", "Paroxysmal atrial fibrillation", "Παροξυσμική κολπική μαρμαρυγή", "I", "Arrhythmia"),
    ("I48.1", "Persistent atrial fibrillation", "Εμμένουσα κολπική μαρμαρυγή", "I", "Arrhythmia"),
    ("I48.2", "Chronic atrial fibrillation", "Χρόνια κολπική μαρμαρυγή", "I", "Arrhythmia"),
    ("I48.91", "Unspecified atrial fibrillation", "Μη καθορισμένη κολπική μαρμαρυγή", "I", "Arrhythmia"),
    ("I48.92", "Unspecified atrial flutter", "Μη καθορισμένος κολπικός πτερυγισμός", "I", "Arrhythmia"),
    ("I49.5", "Sick sinus syndrome", "Σύνδρομο νοσούντος φλεβοκόμβου", "I", "Arrhythmia"),
    ("I50.1", "Left ventricular failure, unspecified", "Αριστερή κοιλιακή ανεπάρκεια", "I", "Heart failure"),
    ("I50.20", "Unspecified systolic heart failure", "Μη καθορισμένη συστολική καρδιακή ανεπάρκεια", "I", "Heart failure"),
    ("I50.22", "Chronic systolic heart failure", "Χρόνια συστολική καρδιακή ανεπάρκεια", "I", "Heart failure"),
    ("I50.30", "Unspecified diastolic heart failure", "Μη καθορισμένη διαστολική καρδιακή ανεπάρκεια", "I", "Heart failure"),
    ("I50.32", "Chronic diastolic heart failure", "Χρόνια διαστολική καρδιακή ανεπάρκεια", "I", "Heart failure"),
    ("I50.9", "Heart failure, unspecified", "Καρδιακή ανεπάρκεια, μη καθορισμένη", "I", "Heart failure"),
    # Hypertension
    ("I10", "Essential (primary) hypertension", "Ιδιοπαθής (πρωτοπαθής) υπέρταση", "I", "Hypertension"),
    ("I11.0", "Hypertensive heart disease with heart failure", "Υπερτασική καρδιοπάθεια με καρδιακή ανεπάρκεια", "I", "Hypertension"),
    ("I11.9", "Hypertensive heart disease without heart failure", "Υπερτασική καρδιοπάθεια χωρίς ΚΑ", "I", "Hypertension"),
    ("I13.0", "Hypertensive heart and kidney disease with heart failure", "Υπερτασική καρδιο-νεφρική νόσος με ΚΑ", "I", "Hypertension"),
]

# =============================================================================
# CPT Cardiology Procedure Codes
# =============================================================================
CPT_CODES = [
    # Echocardiography
    ("93303", "Transthoracic echo complete", "Echocardiography", 3.5),
    ("93304", "Transthoracic echo follow-up/limited", "Echocardiography", 2.0),
    ("93306", "TTE with Doppler complete", "Echocardiography", 4.5),
    ("93307", "TTE with 2D without Doppler", "Echocardiography", 3.0),
    ("93312", "Transesophageal echo (TEE)", "Echocardiography", 6.0),
    ("93314", "TEE during cardiac surgery", "Echocardiography", 5.0),
    ("93350", "Stress echocardiography", "Echocardiography", 5.0),
    # ECG/Monitoring
    ("93000", "Electrocardiogram (12-lead) complete", "ECG/Monitoring", 1.0),
    ("93005", "ECG tracing only", "ECG/Monitoring", 0.5),
    ("93010", "ECG interpretation only", "ECG/Monitoring", 0.5),
    ("93224", "Holter monitor 24-hour recording", "ECG/Monitoring", 3.0),
    ("93225", "Holter monitor recording only", "ECG/Monitoring", 1.5),
    ("93226", "Holter monitor scanning/interpretation", "ECG/Monitoring", 2.0),
    ("93241", "Event monitor 30 days", "ECG/Monitoring", 3.5),
    ("93015", "Exercise stress test complete", "Stress Testing", 4.0),
    ("93016", "Stress test physician supervision only", "Stress Testing", 2.0),
    ("93018", "Stress test interpretation only", "Stress Testing", 2.0),
    # Cardiac Catheterization
    ("93451", "Right heart catheterization", "Catheterization", 8.0),
    ("93452", "Left heart catheterization", "Catheterization", 10.0),
    ("93453", "Combined right and left heart catheterization", "Catheterization", 12.0),
    ("93454", "Coronary angiography without left heart cath", "Catheterization", 8.0),
    ("93456", "Coronary angiography with left heart cath", "Catheterization", 11.0),
    ("93458", "Left heart cath with coronary angiography and LV", "Catheterization", 12.0),
    # PCI (Percutaneous Coronary Intervention)
    ("92920", "PCI single vessel (initial)", "PCI", 15.0),
    ("92921", "PCI single vessel (each additional)", "PCI", 8.0),
    ("92928", "PCI with stent (initial vessel)", "PCI", 18.0),
    ("92929", "PCI with stent (each additional vessel)", "PCI", 10.0),
    ("92937", "PCI with stent in bypass graft", "PCI", 18.0),
    # Electrophysiology
    ("93600", "Bundle of His recording", "Electrophysiology", 6.0),
    ("93609", "Intra-atrial mapping", "Electrophysiology", 8.0),
    ("93613", "Intracardiac electrophysiological 3D mapping", "Electrophysiology", 12.0),
    ("93653", "EP ablation for SVT", "Electrophysiology", 15.0),
    ("93656", "EP ablation for VT", "Electrophysiology", 18.0),
    # Pacemaker/ICD
    ("33206", "Insertion of pacemaker (atrial)", "Pacemaker/ICD", 12.0),
    ("33207", "Insertion of pacemaker (ventricular)", "Pacemaker/ICD", 12.0),
    ("33208", "Insertion of pacemaker (dual chamber)", "Pacemaker/ICD", 14.0),
    ("33249", "Insertion of ICD", "Pacemaker/ICD", 18.0),
    ("33285", "Insertion of loop recorder", "Pacemaker/ICD", 4.0),
    # Cardioversion
    ("92960", "External cardioversion", "Cardioversion", 3.0),
    ("92961", "Internal cardioversion", "Cardioversion", 5.0),
]

# =============================================================================
# HIO Service Codes (Cyprus-specific)
# =============================================================================
HIO_CODES = [
    ("HIO-CARD-001", "Cardiology consultation (new patient)", "Καρδιολογική εξέταση (νέος ασθενής)", "consultation", "CARD", 50.0),
    ("HIO-CARD-002", "Cardiology follow-up", "Καρδιολογική παρακολούθηση", "consultation", "CARD", 35.0),
    ("HIO-CARD-010", "12-lead ECG with interpretation", "ΗΚΓ 12 απαγωγών με ερμηνεία", "diagnostic", "CARD", 25.0),
    ("HIO-CARD-011", "Holter monitor 24h", "Holter 24ωρο", "diagnostic", "CARD", 80.0),
    ("HIO-CARD-012", "Event recorder 7 days", "Καταγραφέας συμβάντων 7 ημερών", "diagnostic", "CARD", 120.0),
    ("HIO-CARD-020", "Transthoracic echocardiogram (TTE)", "Διαθωρακικό υπερηχοκαρδιογράφημα", "diagnostic", "CARD", 95.0),
    ("HIO-CARD-021", "Transesophageal echocardiogram (TEE)", "Διοισοφάγειο υπερηχοκαρδιογράφημα", "diagnostic", "CARD", 180.0),
    ("HIO-CARD-022", "Stress echocardiogram", "Υπερηχοκαρδιογράφημα κόπωσης", "diagnostic", "CARD", 150.0),
    ("HIO-CARD-030", "Exercise stress test (treadmill)", "Δοκιμασία κόπωσης (διάδρομος)", "diagnostic", "CARD", 100.0),
    ("HIO-CARD-040", "Coronary angiography", "Στεφανιογραφία", "interventional", "CARD", 800.0),
    ("HIO-CARD-041", "PCI with single stent", "Αγγειοπλαστική με τοποθέτηση stent", "interventional", "CARD", 2500.0),
    ("HIO-CARD-042", "PCI additional stent", "Αγγειοπλαστική πρόσθετο stent", "interventional", "CARD", 1500.0),
    ("HIO-CARD-050", "Pacemaker implantation (dual chamber)", "Εμφύτευση βηματοδότη (διπλής κοιλότητας)", "interventional", "CARD", 3000.0),
    ("HIO-CARD-051", "ICD implantation", "Εμφύτευση αυτόματου απινιδωτή", "interventional", "CARD", 5000.0),
    ("HIO-CARD-052", "CRT-D implantation", "Εμφύτευση CRT-D", "interventional", "CARD", 7000.0),
    ("HIO-CARD-060", "External cardioversion", "Εξωτερική ηλεκτρική ανάταξη", "interventional", "CARD", 200.0),
    ("HIO-CARD-061", "EP study", "Ηλεκτροφυσιολογική μελέτη", "interventional", "CARD", 1200.0),
    ("HIO-CARD-062", "Catheter ablation (SVT)", "Κατάλυση με καθετήρα (SVT)", "interventional", "CARD", 2000.0),
    ("HIO-CARD-063", "Catheter ablation (AF)", "Κατάλυση με καθετήρα (ΚΜ)", "interventional", "CARD", 4000.0),
    ("HIO-CARD-070", "Ambulatory BP monitoring 24h", "24ωρη καταγραφή αρτηριακής πίεσης", "diagnostic", "CARD", 60.0),
]

# =============================================================================
# ATC Codes (Cardiology-relevant)
# =============================================================================
ATC_CODES = [
    # Statins
    ("C10AA", "HMG CoA reductase inhibitors", 4, "C10A", None),
    ("C10AA01", "Simvastatin", 5, "C10AA", "20mg"),
    ("C10AA03", "Pravastatin", 5, "C10AA", "20mg"),
    ("C10AA05", "Atorvastatin", 5, "C10AA", "20mg"),
    ("C10AA07", "Rosuvastatin", 5, "C10AA", "10mg"),
    # Beta-blockers
    ("C07AB", "Beta blocking agents, selective", 4, "C07A", None),
    ("C07AB02", "Metoprolol", 5, "C07AB", "100mg"),
    ("C07AB05", "Betaxolol", 5, "C07AB", "20mg"),
    ("C07AB07", "Bisoprolol", 5, "C07AB", "5mg"),
    ("C07AB12", "Nebivolol", 5, "C07AB", "5mg"),
    # ACE Inhibitors
    ("C09AA", "ACE inhibitors, plain", 4, "C09A", None),
    ("C09AA02", "Enalapril", 5, "C09AA", "10mg"),
    ("C09AA03", "Lisinopril", 5, "C09AA", "10mg"),
    ("C09AA05", "Ramipril", 5, "C09AA", "5mg"),
    ("C09AA09", "Fosinopril", 5, "C09AA", "20mg"),
    # ARBs
    ("C09CA", "Angiotensin II receptor blockers, plain", 4, "C09C", None),
    ("C09CA01", "Losartan", 5, "C09CA", "50mg"),
    ("C09CA03", "Valsartan", 5, "C09CA", "80mg"),
    ("C09CA04", "Irbesartan", 5, "C09CA", "150mg"),
    ("C09CA06", "Candesartan", 5, "C09CA", "8mg"),
    ("C09CA08", "Olmesartan", 5, "C09CA", "20mg"),
    # Anticoagulants
    ("B01AA", "Vitamin K antagonists", 4, "B01A", None),
    ("B01AA03", "Warfarin", 5, "B01AA", "5mg"),
    ("B01AF", "Direct factor Xa inhibitors", 4, "B01A", None),
    ("B01AF01", "Rivaroxaban", 5, "B01AF", "20mg"),
    ("B01AF02", "Apixaban", 5, "B01AF", "5mg"),
    ("B01AF03", "Edoxaban", 5, "B01AF", "60mg"),
    ("B01AE", "Direct thrombin inhibitors", 4, "B01A", None),
    ("B01AE07", "Dabigatran", 5, "B01AE", "150mg"),
    # Antiplatelets
    ("B01AC", "Platelet aggregation inhibitors", 4, "B01A", None),
    ("B01AC04", "Clopidogrel", 5, "B01AC", "75mg"),
    ("B01AC06", "Acetylsalicylic acid (Aspirin)", 5, "B01AC", "100mg"),
    ("B01AC22", "Prasugrel", 5, "B01AC", "10mg"),
    ("B01AC24", "Ticagrelor", 5, "B01AC", "90mg"),
    # Calcium Channel Blockers
    ("C08CA", "Dihydropyridine derivatives", 4, "C08C", None),
    ("C08CA01", "Amlodipine", 5, "C08CA", "5mg"),
    ("C08CA02", "Felodipine", 5, "C08CA", "5mg"),
    ("C08DA", "Phenylalkylamine derivatives", 4, "C08D", None),
    ("C08DA01", "Verapamil", 5, "C08DA", "240mg"),
    ("C08DB", "Benzothiazepine derivatives", 4, "C08D", None),
    ("C08DB01", "Diltiazem", 5, "C08DB", "120mg"),
    # Diuretics
    ("C03CA", "Sulfonamides, plain (loop)", 4, "C03C", None),
    ("C03CA01", "Furosemide", 5, "C03CA", "40mg"),
    ("C03DA", "Aldosterone antagonists", 4, "C03D", None),
    ("C03DA01", "Spironolactone", 5, "C03DA", "25mg"),
    ("C03DA04", "Eplerenone", 5, "C03DA", "25mg"),
    # Antiarrhythmics
    ("C01BD", "Antiarrhythmics, class III", 4, "C01B", None),
    ("C01BD01", "Amiodarone", 5, "C01BD", "200mg"),
    ("C01BD07", "Dronedarone", 5, "C01BD", "400mg"),
    # Nitrates
    ("C01DA", "Organic nitrates", 4, "C01D", None),
    ("C01DA02", "Glyceryl trinitrate", 5, "C01DA", "0.5mg"),
    ("C01DA08", "Isosorbide dinitrate", 5, "C01DA", "20mg"),
    ("C01DA14", "Isosorbide mononitrate", 5, "C01DA", "60mg"),
    # Heart failure specific
    ("C01EB", "Other cardiac preparations", 4, "C01E", None),
    ("C09DX04", "Sacubitril/Valsartan (Entresto)", 5, "C09DX", "97/103mg"),
    ("A10BK", "SGLT2 inhibitors", 4, "A10B", None),
    ("A10BK01", "Dapagliflozin", 5, "A10BK", "10mg"),
    ("A10BK03", "Empagliflozin", 5, "A10BK", "10mg"),
]

# =============================================================================
# LOINC Codes (Cardiac Labs)
# =============================================================================
LOINC_CODES = [
    ("2157-6", "Creatine kinase-MB [Mass/volume]", "CK-MB", "CK-MB", "Chemistry"),
    ("6598-7", "Troponin T.cardiac [Mass/volume]", "cTnT", "Troponin T", "Chemistry"),
    ("10839-9", "Troponin I.cardiac [Mass/volume]", "cTnI", "Troponin I", "Chemistry"),
    ("49563-0", "Troponin I.cardiac high sensitivity", "hs-cTnI", "Troponin I hs", "Chemistry"),
    ("89579-7", "Troponin T.cardiac high sensitivity", "hs-cTnT", "Troponin T hs", "Chemistry"),
    ("30934-4", "NT-proBNP [Mass/volume]", "NT-proBNP", "NT-proBNP", "Chemistry"),
    ("42637-9", "BNP [Mass/volume]", "BNP", "BNP", "Chemistry"),
    ("2093-3", "Cholesterol [Mass/volume]", "TC", "Total Cholesterol", "Chemistry"),
    ("2571-8", "Triglyceride [Mass/volume]", "TG", "Triglycerides", "Chemistry"),
    ("2085-9", "HDL cholesterol [Mass/volume]", "HDL", "HDL Cholesterol", "Chemistry"),
    ("13457-7", "LDL cholesterol (calculated)", "LDL-C", "LDL Cholesterol", "Chemistry"),
    ("43838-2", "Lipoprotein(a) [Mass/volume]", "Lp(a)", "Lipoprotein(a)", "Chemistry"),
    ("2160-0", "Creatinine [Mass/volume]", "Creat", "Creatinine", "Chemistry"),
    ("33914-3", "eGFR (CKD-EPI)", "eGFR", "eGFR", "Chemistry"),
    ("6299-2", "INR", "INR", "INR", "Coagulation"),
    ("3173-2", "aPTT", "aPTT", "aPTT", "Coagulation"),
    ("14979-9", "D-dimer [Mass/volume]", "D-dimer", "D-dimer", "Coagulation"),
    ("2951-2", "Sodium [Moles/volume]", "Na", "Sodium", "Chemistry"),
    ("2823-3", "Potassium [Moles/volume]", "K", "Potassium", "Chemistry"),
    ("2345-7", "Glucose [Mass/volume]", "Gluc", "Glucose", "Chemistry"),
    ("4548-4", "Hemoglobin A1c", "HbA1c", "HbA1c", "Chemistry"),
    ("1988-5", "CRP [Mass/volume]", "CRP", "C-Reactive Protein", "Chemistry"),
    ("30522-7", "hs-CRP [Mass/volume]", "hs-CRP", "hs-CRP", "Chemistry"),
    ("2276-4", "Ferritin [Mass/volume]", "Ferr", "Ferritin", "Chemistry"),
    ("718-7", "Hemoglobin [Mass/volume]", "Hgb", "Hemoglobin", "Hematology"),
    ("3094-0", "BUN [Mass/volume]", "BUN", "Blood Urea Nitrogen", "Chemistry"),
    ("2532-0", "Lactate dehydrogenase [U/volume]", "LDH", "LDH", "Chemistry"),
    ("1742-6", "ALT [U/volume]", "ALT", "ALT", "Chemistry"),
    ("1920-8", "AST [U/volume]", "AST", "AST", "Chemistry"),
    ("3084-1", "Uric acid [Mass/volume]", "UA", "Uric Acid", "Chemistry"),
]

# =============================================================================
# Gesy Medications (HIO Product Registry)
# =============================================================================
GESY_MEDICATIONS = [
    # Statins
    ("HIO-MED-001", "C10AA05", "Lipitor", "Atorvastatin", "10mg", "tablet", 30, "Pfizer", 12.50, False),
    ("HIO-MED-002", "C10AA05", "Lipitor", "Atorvastatin", "20mg", "tablet", 30, "Pfizer", 18.00, False),
    ("HIO-MED-003", "C10AA05", "Lipitor", "Atorvastatin", "40mg", "tablet", 30, "Pfizer", 25.00, False),
    ("HIO-MED-004", "C10AA05", "Lipitor", "Atorvastatin", "80mg", "tablet", 30, "Pfizer", 30.00, False),
    ("HIO-MED-005", "C10AA07", "Crestor", "Rosuvastatin", "5mg", "tablet", 28, "AstraZeneca", 15.00, False),
    ("HIO-MED-006", "C10AA07", "Crestor", "Rosuvastatin", "10mg", "tablet", 28, "AstraZeneca", 20.00, False),
    ("HIO-MED-007", "C10AA07", "Crestor", "Rosuvastatin", "20mg", "tablet", 28, "AstraZeneca", 28.00, False),
    ("HIO-MED-008", "C10AA01", "Zocor", "Simvastatin", "20mg", "tablet", 28, "MSD", 10.00, False),
    ("HIO-MED-009", "C10AA01", "Zocor", "Simvastatin", "40mg", "tablet", 28, "MSD", 14.00, False),
    # Beta-blockers
    ("HIO-MED-010", "C07AB07", "Concor", "Bisoprolol", "2.5mg", "tablet", 30, "Merck", 8.00, False),
    ("HIO-MED-011", "C07AB07", "Concor", "Bisoprolol", "5mg", "tablet", 30, "Merck", 10.00, False),
    ("HIO-MED-012", "C07AB07", "Concor", "Bisoprolol", "10mg", "tablet", 30, "Merck", 12.00, False),
    ("HIO-MED-013", "C07AB02", "Betaloc ZOK", "Metoprolol succinate", "50mg", "tablet XL", 28, "AstraZeneca", 9.00, False),
    ("HIO-MED-014", "C07AB02", "Betaloc ZOK", "Metoprolol succinate", "100mg", "tablet XL", 28, "AstraZeneca", 12.00, False),
    ("HIO-MED-015", "C07AB12", "Nebilet", "Nebivolol", "5mg", "tablet", 28, "Menarini", 14.00, False),
    # ACE Inhibitors
    ("HIO-MED-020", "C09AA05", "Tritace", "Ramipril", "2.5mg", "tablet", 28, "Sanofi", 6.00, False),
    ("HIO-MED-021", "C09AA05", "Tritace", "Ramipril", "5mg", "tablet", 28, "Sanofi", 8.00, False),
    ("HIO-MED-022", "C09AA05", "Tritace", "Ramipril", "10mg", "tablet", 28, "Sanofi", 10.00, False),
    ("HIO-MED-023", "C09AA03", "Zestril", "Lisinopril", "5mg", "tablet", 28, "AstraZeneca", 5.00, False),
    ("HIO-MED-024", "C09AA03", "Zestril", "Lisinopril", "10mg", "tablet", 28, "AstraZeneca", 7.00, False),
    ("HIO-MED-025", "C09AA03", "Zestril", "Lisinopril", "20mg", "tablet", 28, "AstraZeneca", 9.00, False),
    # ARBs
    ("HIO-MED-030", "C09CA03", "Diovan", "Valsartan", "80mg", "tablet", 28, "Novartis", 12.00, False),
    ("HIO-MED-031", "C09CA03", "Diovan", "Valsartan", "160mg", "tablet", 28, "Novartis", 16.00, False),
    ("HIO-MED-032", "C09CA01", "Cozaar", "Losartan", "50mg", "tablet", 28, "MSD", 10.00, False),
    ("HIO-MED-033", "C09CA01", "Cozaar", "Losartan", "100mg", "tablet", 28, "MSD", 14.00, False),
    ("HIO-MED-034", "C09CA06", "Atacand", "Candesartan", "8mg", "tablet", 28, "AstraZeneca", 11.00, False),
    ("HIO-MED-035", "C09CA06", "Atacand", "Candesartan", "16mg", "tablet", 28, "AstraZeneca", 15.00, False),
    # Anticoagulants
    ("HIO-MED-040", "B01AA03", "Coumadin", "Warfarin", "5mg", "tablet", 100, "Bristol-Myers Squibb", 8.00, False),
    ("HIO-MED-041", "B01AF02", "Eliquis", "Apixaban", "2.5mg", "tablet", 60, "Bristol-Myers Squibb", 65.00, False),
    ("HIO-MED-042", "B01AF02", "Eliquis", "Apixaban", "5mg", "tablet", 60, "Bristol-Myers Squibb", 65.00, False),
    ("HIO-MED-043", "B01AF01", "Xarelto", "Rivaroxaban", "15mg", "tablet", 28, "Bayer", 55.00, False),
    ("HIO-MED-044", "B01AF01", "Xarelto", "Rivaroxaban", "20mg", "tablet", 28, "Bayer", 55.00, False),
    ("HIO-MED-045", "B01AE07", "Pradaxa", "Dabigatran", "110mg", "capsule", 60, "Boehringer", 60.00, False),
    ("HIO-MED-046", "B01AE07", "Pradaxa", "Dabigatran", "150mg", "capsule", 60, "Boehringer", 60.00, False),
    ("HIO-MED-047", "B01AF03", "Lixiana", "Edoxaban", "30mg", "tablet", 28, "Daiichi Sankyo", 52.00, False),
    ("HIO-MED-048", "B01AF03", "Lixiana", "Edoxaban", "60mg", "tablet", 28, "Daiichi Sankyo", 52.00, False),
    # Antiplatelets
    ("HIO-MED-050", "B01AC06", "Aspirin Cardio", "Acetylsalicylic acid", "100mg", "tablet", 30, "Bayer", 3.00, False),
    ("HIO-MED-051", "B01AC04", "Plavix", "Clopidogrel", "75mg", "tablet", 28, "Sanofi", 22.00, False),
    ("HIO-MED-052", "B01AC24", "Brilique", "Ticagrelor", "90mg", "tablet", 56, "AstraZeneca", 55.00, False),
    ("HIO-MED-053", "B01AC22", "Efient", "Prasugrel", "10mg", "tablet", 28, "Eli Lilly", 48.00, False),
    # Calcium Channel Blockers
    ("HIO-MED-060", "C08CA01", "Norvasc", "Amlodipine", "5mg", "tablet", 30, "Pfizer", 6.00, False),
    ("HIO-MED-061", "C08CA01", "Norvasc", "Amlodipine", "10mg", "tablet", 30, "Pfizer", 8.00, False),
    ("HIO-MED-062", "C08DA01", "Isoptin", "Verapamil", "240mg", "tablet SR", 30, "Abbott", 10.00, False),
    ("HIO-MED-063", "C08DB01", "Diltiazem HCl", "Diltiazem", "120mg", "capsule SR", 30, "Various", 8.00, False),
    # Diuretics
    ("HIO-MED-070", "C03CA01", "Lasix", "Furosemide", "40mg", "tablet", 20, "Sanofi", 3.00, False),
    ("HIO-MED-071", "C03DA01", "Aldactone", "Spironolactone", "25mg", "tablet", 30, "Pfizer", 5.00, False),
    ("HIO-MED-072", "C03DA04", "Inspra", "Eplerenone", "25mg", "tablet", 28, "Pfizer", 35.00, False),
    ("HIO-MED-073", "C03DA04", "Inspra", "Eplerenone", "50mg", "tablet", 28, "Pfizer", 40.00, False),
    # Antiarrhythmics
    ("HIO-MED-080", "C01BD01", "Cordarone", "Amiodarone", "200mg", "tablet", 30, "Sanofi", 8.00, False),
    ("HIO-MED-081", "C01BD07", "Multaq", "Dronedarone", "400mg", "tablet", 60, "Sanofi", 85.00, True),
    # Heart Failure (ARNI, SGLT2i)
    ("HIO-MED-090", "C09DX04", "Entresto", "Sacubitril/Valsartan", "24/26mg", "tablet", 56, "Novartis", 95.00, True),
    ("HIO-MED-091", "C09DX04", "Entresto", "Sacubitril/Valsartan", "49/51mg", "tablet", 56, "Novartis", 95.00, True),
    ("HIO-MED-092", "C09DX04", "Entresto", "Sacubitril/Valsartan", "97/103mg", "tablet", 56, "Novartis", 95.00, True),
    ("HIO-MED-093", "A10BK01", "Forxiga", "Dapagliflozin", "10mg", "tablet", 28, "AstraZeneca", 45.00, True),
    ("HIO-MED-094", "A10BK03", "Jardiance", "Empagliflozin", "10mg", "tablet", 28, "Boehringer", 45.00, True),
    # Nitrates
    ("HIO-MED-095", "C01DA02", "GTN Spray", "Glyceryl trinitrate", "0.4mg/dose", "spray", 1, "Various", 5.00, False),
    ("HIO-MED-096", "C01DA14", "Imdur", "Isosorbide mononitrate", "60mg", "tablet SR", 28, "AstraZeneca", 12.00, False),
]


async def seed_all() -> None:
    """Insert all seed data into coding tables."""
    async with async_session_factory() as session:
        # Check if data already exists
        result = await session.execute(text("SELECT COUNT(*) FROM icd10_codes"))
        count = result.scalar()
        if count and count > 0:
            print(f"Coding tables already seeded ({count} ICD-10 codes). Skipping.")
            return

        print("Seeding medical coding tables...")

        # ICD-10
        for code, desc_en, desc_el, chapter, category in ICD10_CODES:
            await session.execute(
                text("""
                    INSERT INTO icd10_codes (code, description_en, description_el, chapter, category)
                    VALUES (:code, :desc_en, :desc_el, :chapter, :category)
                    ON CONFLICT (code) DO NOTHING
                """),
                {"code": code, "desc_en": desc_en, "desc_el": desc_el, "chapter": chapter, "category": category},
            )
        print(f"  Inserted {len(ICD10_CODES)} ICD-10 codes")

        # CPT
        for code, description, category, rv in CPT_CODES:
            await session.execute(
                text("""
                    INSERT INTO cpt_codes (code, description, category, relative_value)
                    VALUES (:code, :desc, :category, :rv)
                    ON CONFLICT (code) DO NOTHING
                """),
                {"code": code, "desc": description, "category": category, "rv": rv},
            )
        print(f"  Inserted {len(CPT_CODES)} CPT codes")

        # HIO Service Codes
        for code, desc_en, desc_el, stype, specialty, price in HIO_CODES:
            await session.execute(
                text("""
                    INSERT INTO hio_service_codes (code, description_en, description_el, service_type, specialty_code, base_price_eur)
                    VALUES (:code, :desc_en, :desc_el, :stype, :specialty, :price)
                    ON CONFLICT (code) DO NOTHING
                """),
                {"code": code, "desc_en": desc_en, "desc_el": desc_el, "stype": stype, "specialty": specialty, "price": price},
            )
        print(f"  Inserted {len(HIO_CODES)} HIO service codes")

        # ATC Codes
        for code, name, level, parent, ddd in ATC_CODES:
            await session.execute(
                text("""
                    INSERT INTO atc_codes (code, name, level, parent_code, ddd)
                    VALUES (:code, :name, :level, :parent, :ddd)
                    ON CONFLICT (code) DO NOTHING
                """),
                {"code": code, "name": name, "level": level, "parent": parent, "ddd": ddd},
            )
        print(f"  Inserted {len(ATC_CODES)} ATC codes")

        # LOINC Codes
        for code, long_name, short_name, component, class_type in LOINC_CODES:
            await session.execute(
                text("""
                    INSERT INTO loinc_codes (code, long_name, short_name, component, class_type)
                    VALUES (:code, :long_name, :short_name, :component, :class_type)
                    ON CONFLICT (code) DO NOTHING
                """),
                {"code": code, "long_name": long_name, "short_name": short_name, "component": component, "class_type": class_type},
            )
        print(f"  Inserted {len(LOINC_CODES)} LOINC codes")

        # Gesy Medications
        for hio_id, atc, brand, generic, strength, form, pack, mfr, price, pre_auth in GESY_MEDICATIONS:
            await session.execute(
                text("""
                    INSERT INTO gesy_medications (hio_product_id, atc_code, brand_name, generic_name, strength, form, pack_size, manufacturer, price_eur, requires_pre_auth)
                    VALUES (:hio_id, :atc, :brand, :generic, :strength, :form, :pack, :mfr, :price, :pre_auth)
                    ON CONFLICT (hio_product_id) DO NOTHING
                """),
                {"hio_id": hio_id, "atc": atc, "brand": brand, "generic": generic, "strength": strength,
                 "form": form, "pack": pack, "mfr": mfr, "price": price, "pre_auth": pre_auth},
            )
        print(f"  Inserted {len(GESY_MEDICATIONS)} Gesy medications")

        await session.commit()
        print("Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_all())
