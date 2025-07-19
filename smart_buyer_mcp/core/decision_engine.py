from datetime import datetime

class DecisionEngine:
    def decide(self, product_info):
        # Placeholder: Simple rule-based decision
        price = product_info.get('price')
        verdict = "Buy" if price and float(price.replace(',', '').replace('₹', '').strip()) < 1000 else "Wait"
        return {
            "verdict": verdict,
            "timestamp": datetime.utcnow().isoformat()
        } 