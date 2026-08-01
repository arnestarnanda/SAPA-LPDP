import re
import html
from typing import Dict, Any

class InjectionDetector:
    def __init__(self):
        self.dangerous_patterns = [
            re.compile(r"(?i)ignore all previous"),
            re.compile(r"(?i)system prompt"),
            re.compile(r"(?i)new instruction"),
            re.compile(r"(?i)forget previous"),
            re.compile(r"(?i)bypass"),
            re.compile(r"(?i)you are hacked"),
            re.compile(r"(?i)override instructions"),
            re.compile(r"(?i)jailbreak")
        ]

    def detect(self, text: str) -> Dict[str, Any]:
        for pattern in self.dangerous_patterns:
            if pattern.search(text):
                return {
                    "is_safe": False,
                    "action": "BLOCK",
                    "reason": f"Detected suspicious prompt injection pattern: '{pattern.pattern}'"
                }
        return {"is_safe": True, "action": "ALLOW", "reason": ""}

class InputValidator:
    def __init__(self):
        self.detector = InjectionDetector()

    def validate(self, user_input: str) -> Dict[str, Any]:
        if not user_input or not user_input.strip():
            return {"valid": False, "sanitized_input": "", "reason": "Input kosong"}
        
        if len(user_input) > 32000:
            return {"valid": False, "sanitized_input": "", "reason": "Input melebihi batas 32,000 karakter"}
            
        # Sanitize HTML tags for safety
        sanitized = html.escape(user_input)
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        # Check for injection attacks
        injection_check = self.detector.detect(sanitized)
        if not injection_check["is_safe"]:
            return {"valid": False, "sanitized_input": sanitized, "reason": injection_check["reason"]}
            
        return {"valid": True, "sanitized_input": sanitized, "reason": ""}

class OutputValidator:
    def __init__(self):
        self.sensitive_patterns = {
            "api_key": re.compile(r"(?i)(sk-[a-zA-Z0-9]{20,}|AIzaSy[a-zA-Z0-9_-]{33})"),
            "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
            "phone": re.compile(r"(\+62|08)[0-9]{8,11}"),
            "nik": re.compile(r"\b[0-9]{16}\b")
        }

    def validate(self, text: str) -> str:
        filtered = text
        for key, pattern in self.sensitive_patterns.items():
            filtered = pattern.sub(f"[{key.UPPER() if hasattr(key, 'UPPER') else key.upper()}_REDACTED]", filtered)
        return filtered

class GuardrailSystem:
    def __init__(self):
        self.input_validator = InputValidator()
        self.output_validator = OutputValidator()

    def process_request(self, user_input: str) -> Dict[str, Any]:
        # Layer 1 & 4 (Input validation & Prompt Protection checks)
        return self.input_validator.validate(user_input)
        
    def validate_output(self, raw_output: str) -> str:
        # Layer 3 (Output validation & PII Redaction)
        return self.output_validator.validate(raw_output)
