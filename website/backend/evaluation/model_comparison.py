from langchain_community.llms import Ollama
from src.classify_prompt_template import classify_prompt
import time
from typing import Dict, List

class ModelBenchmark:
    def __init__(self):
        self.models = {
            "gemma3:270m": Ollama(model="gemma3:270m"),
            "mistral:7b": Ollama(model="gemma3:270m")
        }
    
    def classify_with_model(self, model, message: str) -> str:
        """Classify persona using the given model"""
        classification_prompt = classify_prompt.format(message=message)
        persona = model.invoke(classification_prompt).strip().lower()
        
        # Validate persona
        valid_personas = {"verbose", "reserved", "oversharer"}
        if persona not in valid_personas:
            persona = "verbose"  # Default fallback
        
        return persona
    
    def benchmark_response_time(self, queries: List[str]) -> Dict:
        """Compare response times"""
        results = {}
        
        for model_name, model in self.models.items():
            times = []
            for query in queries:
                try:
                    start = time.time()
                    response = model.invoke(query)
                    end = time.time()
                    times.append(end - start)
                except Exception as e:
                    print(f"Error with {model_name}: {e}")
                    times.append(0)
            
            if times:
                results[model_name] = {
                    "avg_time": round(sum(times) / len(times), 3),
                    "min_time": round(min(times), 3),
                    "max_time": round(max(times), 3)
                }
        
        return results
    
    def benchmark_persona_accuracy(self, test_cases: List[Dict]) -> Dict:
        """
        test_cases = [
            {"message": "I feel so overwhelmed...", "expected": "oversharer"},
            {"message": "Fine.", "expected": "reserved"},
            ...
        ]
        """
        results = {}
        
        for model_name, model in self.models.items():
            correct = 0
            total = len(test_cases)
            
            for case in test_cases:
                try:
                    prediction = self.classify_with_model(model, case["message"])
                    if prediction == case["expected"]:
                        correct += 1
                except Exception as e:
                    print(f"Error classifying with {model_name}: {e}")
            
            results[model_name] = {
                "accuracy": round(correct / total, 3) if total > 0 else 0,
                "correct": correct,
                "total": total
            }
        
        return results