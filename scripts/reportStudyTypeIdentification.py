from transformers import pipeline
import threading

class StudyTypeProcessor:
    _instance = None
    _lock = threading.Lock()

    STUDY_TYPES = [
        "liver",
        "gallbladder",
        "kidney",
        "uterus",
        "ovary",
        "spleen",
        "pancreas",
        "urinary bladder",
        "prostate",
        "thyroid",
        "breast"
    ]

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        print("[STUDY_TYPE] Loading BART MNLI model...")
        self.classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=-1,
            multi_label=True
        )
        print("[STUDY_TYPE] Model loaded and ready")

    def identify(self, text: str, confidence_threshold=0.5):
        text = text.strip()
        if len(text) < 3:
            return False, "No US Study Type Found"

        output = self.classifier(
            text,
            self.STUDY_TYPES,
            multi_label=True
        )

        detected = {
            label: round(score, 3)
            for label, score in zip(output["labels"], output["scores"])
            if score >= confidence_threshold
        }

        if not detected:
            return False, "No US Study Type Found"

        best_study = max(detected, key=detected.get)
        return True, best_study.upper()
