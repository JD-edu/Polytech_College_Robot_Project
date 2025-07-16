import json

json_string = """
{
  "shapes": [
    {
      "shape": "square",
      "description": [
        {
          "side": "approximately 150 pixels"
        }
      ],
      "bounding_box": {
        "x": 20,
        "y": 20,
        "width": 150,
        "height": 150
      }
    },
    {
      "shape": "circle",
      "description": [
        {
          "radius": "approximately 80 pixels"
        }
      ],
      "bounding_box": {
        "x": 200,
        "y": 20,
        "width": 160,
        "height": 160
      }
    },
    {
      "shape": "triangle",
      "description": [
        {
          "side1": "approximately 170 pixels"
        },
        {
          "side2": "approximately 170 pixels"
        },
        {
          "side3": "approximately 170 pixels"
        },
        {
          "vertex1": "60 degrees"
        },
        {
          "vertex2": "60 degrees"
        },
        {
          "vertex3": "60 degrees"
        }
      ],
      "bounding_box": {
        "x": 400,
        "y": 20,
        "width": 170,
        "height": 150
      }
    },
    {
      "shape": "pentagon",
      "description": [
        {
          "side1": "approximately 80 pixels"
        },
        {
          "side2": "approximately 80 pixels"
        },
        {
          "side3": "approximately 80 pixels"
        },
        {
          "side4": "approximately 80 pixels"
        },
        {
          "side5": "approximately 80 pixels"
        }
      ],
      "bounding_box": {
        "x": 20,
        "y": 200,
        "width": 150,
        "height": 130
      }
    },
    {
      "shape": "ellipse",
      "description": [
        {
          "major_axis_radius": "approximately 80 pixels"
        },
        {
          "minor_axis_radius": "approximately 60 pixels"
        }
      ],
      "bounding_box": {
        "x": 200,
        "y": 180,
        "width": 160,
        "height": 140
      }
    },
    {
      "shape": "rectangle",
      "description": [
        {
          "side1": "approximately 180 pixels"
        },
        {
          "side2": "approximately 80 pixels"
        },
        {
          "vertex_angle": "90 degrees"
        }
      ],
      "bounding_box": {
        "x": 400,
        "y": 200,
        "width": 180,
        "height": 80
      }
    }
  ]
}
"""

try:
    data = json.loads(json_string)

    # The parsed JSON data is now a Python dictionary
    print(data)
    #print(type(data))
    
    # Accessing specific elements:
    shapes_list = data['shapes']
    #print(shapes_list)
    print("\nAll shapes:")
    for shape_data in shapes_list:
        print(f"  Shape: {shape_data['shape']}")
    
    # Accessing the bounding box of the all shape:
    for i in range(len(shapes_list)):
        square_bbox = shapes_list[i]['bounding_box']
        print(shapes_list[i]['shape'])
        print(f"  x: {square_bbox['x']}")
        print(f"  y: {square_bbox['y']}")
        print(f"  width: {square_bbox['width']}")
        print(f"  height: {square_bbox['height']}")
    
    # Accessing the description of all shapes
    for i in range(len(shapes_list)):
        triangle_description = shapes_list[i]['description']
        print(shapes_list[i]['shape'])
        for item in triangle_description:
            print(f"  {list(item.keys())[0]}: {list(item.values())[0]}")
    
except json.JSONDecodeError as e:
    print(f"Error decoding JSON: {e}")
    print(f"Problematic JSON string: {json_string}")