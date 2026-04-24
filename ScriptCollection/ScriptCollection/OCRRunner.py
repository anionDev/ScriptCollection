class OCRRunner:
    
    def __enter__(self):
        print("Resource opened")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Resource closed")