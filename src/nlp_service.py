import re

class NLPProcessor:
    def __init__(self, db_service=None):
        self.db_service = db_service

    def extract_data(self, text):
        """
        Extracts product data from text.
        Supports multiple items separated by 'and', 'و', ',', or newlines.
        """
        # Split text into potential item segments
        # Split by newlines, commas, "and", "و"
        segments = re.split(r'\n|,| and | و ', text)
        
        items = []
        
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue
                
            item_data = self._process_segment(segment)
            if item_data:
                items.append(item_data)
        
        return {
            "customer_id": None, # To be filled by handler
            "items": items,
            "raw_text": text
        }

    def _process_segment(self, text):
        data = {
            "product_name": None,
            "quantity": 1,
            "price": 0.0,
            "total": 0.0,
            "specs": "Standard",
            "found_in_db": False
        }
        
        # Extract Quantity
        qty_match = re.search(r'(\d+)\s*(?:pieces|pcs|items|units|قطع|حبة|حبات)?', text, re.IGNORECASE)
        if qty_match:
            try:
                data['quantity'] = int(qty_match.group(1))
            except ValueError:
                data['quantity'] = 1
        
        # Clean text to find product name
        clean_text = text
        # Remove quantity
        if qty_match:
            clean_text = clean_text.replace(qty_match.group(0), "")
            
        # Remove common words
        for word in ["i want", "i need", "please", "order", "اريد", "ابغى", "احتاج", "طلب", "من فضلك"]:
            clean_text = clean_text.replace(word, "")
            
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        if not clean_text:
            return None

        # Database Lookup
        if self.db_service:
            db_product = self.db_service.get_product_by_name(clean_text)
            if db_product:
                data['product_name'] = db_product['name']
                data['price'] = db_product['price']
                data['specs'] = db_product['description']
                data['found_in_db'] = True
            else:
                data['product_name'] = clean_text
        else:
            data['product_name'] = clean_text
            
        # Calculate total
        data['total'] = data['quantity'] * data['price']
        
        return data
