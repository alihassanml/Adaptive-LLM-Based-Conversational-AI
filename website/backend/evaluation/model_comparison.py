from langchain_community.llms import Ollama
import time
from typing import Dict, List

class ModelBenchmark:
    def __init__(self):
        self.models = {
            "gemma3:270m": Ollama(model="gemma3:270m"),
            "mistral:7b": Ollama(model="mistral:latest")
        }
    
    def benchmark_response_time(self, queries: List[str]) -> Dict:
        """Compare response times"""
        results = {}
        
        for model_name, model in self.models.items():
            times = []
            for query in queries:
                start = time.time()
                response = model.invoke(query)
                end = time.time()
                times.append(end - start)
            
            results[model_name] = {
                "avg_time": sum(times) / len(times),
                "min_time": min(times),
                "max_time": max(times)
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
            for case in test_cases:
                prediction = self.classify_with_model(model, case["message"])
                if prediction == case["expected"]:
                    correct += 1
            
            results[model_name] = {
                "accuracy": correct / len(test_cases),
                "correct": correct,
                "total": len(test_cases)
            }
        
        return results

