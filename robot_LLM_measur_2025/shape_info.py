import json

class ShapeInfo:
    def __init__(self, shape_data):
        self.shape_data = shape_data
        self.shape = shape_data.get("shape")
        self.color = shape_data.get("color")
        self.description = shape_data.get("description", [])
        self.bounding_box = shape_data.get("bounding_box", {})

    def __str__(self):
        return f"Shape: {self.shape}, Color: {self.color}, Bounding Box: {self.bounding_box}"
    
    '''
    이 클래스 함수는 하나의 도형 attribute 데이터를 출력함  
    입력: 없음. self.shape_data를 이용함. self.shape_data는 JSON에서 뽑은 오브젝트 
    출력: self.shape_data를 츨력함  
    '''
    def print_shape_info(self):
        print(f"Shape: {self.shape_data['shape']}")
        shape_description = self.shape_data['description']
        print("Description")
        for item in shape_description:
            print(f"  {list(item.keys())[0]}: {list(item.values())[0]}")
        print("Bounding box")
        print(f"  x: {self.bounding_box['x']}")
        print(f"  y: {self.bounding_box['y']}")
        print(f"  width: {self.bounding_box['width']}")
        print(f"  height: {self.bounding_box['height']}")
        print("  ")
    
    '''
    이 클래스 함수는 하나의 도형 attribute 데이터를 출력이 가능한 문자열로 만들어 줌 
    입력: 없음. self.shape_data를 이용함. self.shape_data는 JSON에서 뽑은 오브젝트 
    출력: self.shape_data는 JSON 오브젝트이므로 이것을 문자열로 변경 
    '''
    def make_string_shape_info(self):
        temp = f"Shape: {self.shape_data['shape']}\n"
        shape_description = self.shape_data['description']
        temp += "Description\n"
        for item in shape_description:
            temp += f"  {list(item.keys())[0]}: {list(item.values())[0]}\n"
        temp += "Bounding box\n"
        temp += f"  x: {self.bounding_box['x']}\n"
        temp += f"  y: {self.bounding_box['y']}\n"
        temp += f"  width: {self.bounding_box['width']}\n"
        temp += f"  height: {self.bounding_box['height']}\n"
        temp += "  \n"
        return temp

if __name__ == "__main__":
    json_string = """
{
    "shapes": [
        {
            "shape": "rounded square",
            "description": [
                {
                    "side": "approximately 450 pixels",
                    "corners": "rounded"
                }
            ],
            "bounding_box": {
                "x": 36,
                "y": 31,
                "width": 442,
                "height": 437
            }
        },
        {
            "shape": "circle",
            "description": [
                {
                    "radius": "approximately 50 pixels"
                }
            ],
            "bounding_box": {
                "x": 59,
                "y": 54,
                "width": 101,
                "height": 101
            }
        },
        {
            "shape": "square",
            "description": [
                {
                    "side": "approximately 70 pixels"
                }
            ],
            "bounding_box": {
                "x": 312,
                "y": 56,
                "width": 92,
                "height": 92
            }
        },
        {
            "shape": "square",
            "description": [
                {
                    "side": "approximately 70 pixels"
                }
            ],
            "bounding_box": {
                "x": 61,
                "y": 300,
                "width": 86,
                "height": 86
            }
        },
        {
            "shape": "circle",
            "description": [
                {
                    "radius": "approximately 50 pixels"
                }
            ],
            "bounding_box": {
                "x": 317,
                "y": 308,
                "width": 100,
                "height": 100
            }
        }
    ]
}
"""
    try:
        data = json.loads(json_string)
        shapes_list = data['shapes']
        shapes_class_list = [] 

        for i in range(len(shapes_list)):
            s1 = ShapeInfo(shapes_list[i])
            shapes_class_list.append(s1)

        #for s1 in shapes_class_list:
        #    s1.print_shape_info()
        shape_info_string = ""
        for s1 in shapes_class_list:
            shape_info_string += s1.make_string_shape_info()
        print(shape_info_string)

    
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        print(f"Problematic JSON string: {json_string}")
