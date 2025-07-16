import json 

class ShapeInfoImage:
    def __init__(self, shape_data):
        self.shape_data = shape_data
        self.id = shape_data.get("id")
        self.type = shape_data.get("type")
        self.location = shape_data.get("location")
        self.center = shape_data.get("center_coordinates_relative", {})
    
    def print_shape_info(self):
        print(f"id: {self.id}")
        print(f"type: {self.type}")
        print(f"location: {self.location}")
        print(f"  x: {self.center['x']}")
        print(f"  y: {self.center['y']}")
        

if __name__ == "__main__":
    json_string = """
        {
            "shapes": [
                {
                    "id": "1",
                    "type": "circle",
                    "location": "top-left",
                    "center_coordinates_relative": {
                        "x": 0.30,
                        "y": 0.30
                    }
                },
                {
                    "id": "2",
                    "type": "circle",
                    "location": "bottom-left",
                    "center_coordinates_relative": {
                        "x": 0.30,
                        "y": 0.70
                    }
                },
                {
                    "id": "3",
                    "type": "square",
                    "location": "top-right",
                    "center_coordinates_relative": {
                        "x": 0.72,
                        "y": 0.28
                    }
                },
                {
                    "id": "4",
                    "type": "square",
                    "location": "bottom-right",
                    "center_coordinates_relative": {
                        "x": 0.72,
                        "y": 0.72
                    }
                },
                {
                    "id": "5",
                    "type": "oval",
                    "location": "center-right",
                    "center_coordinates_relative": {
                        "x": 0.62,
                        "y": 0.55
                    }
                }
            ]
        }
    """
    try: 
        data = json.loads(json_string)
        #print(data)
        shapes_list = data["shapes"]
        #print(shapes_list)
        shapes_class_list = []

        for i in range(len(shapes_list)):
            s1 = ShapeInfoImage(shapes_list[i])
            shapes_class_list.append(s1)
            #print(s1.center["x"])
            s1.print_shape_info()
        
        
        
    
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        print(f"Problematic JSON string: {json_string}")


            