from src.models.domain import PlaceExtract

class DiffEngine:
    """Motor de diferencias para comparar el estado actual vs el nuevo extraído."""
    
    @staticmethod
    def compare(old_data: dict, new_data: PlaceExtract) -> dict:
        diff = {}
        new_dict = new_data.model_dump(exclude_none=True)
        
        for key, new_val in new_dict.items():
            old_val = old_data.get(key)
            if old_val != new_val:
                diff[key] = new_val
                
        return diff
