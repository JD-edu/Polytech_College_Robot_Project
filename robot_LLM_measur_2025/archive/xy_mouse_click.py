import cv2

# 마우스 이벤트를 처리할 콜백 함수
def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:  # 왼쪽 마우스 버튼 클릭 시
        print(f"마우스 클릭 좌표: ({x}, {y})")
        # 필요하다면 클릭한 위치에 원을 그리거나 텍스트를 추가할 수 있습니다.
        # cv2.circle(img, (x, y), 5, (0, 255, 0), -1)
        # cv2.imshow('Image', img)

# 0번 카메라 또는 이미지 파일을 로드
# 카메라를 사용하려면 0 대신 카메라 인덱스를 입력하세요 (예: cv2.VideoCapture(0))
# 이미지를 사용하려면 'your_image.jpg' 대신 이미지 파일 경로를 입력하세요.
# 여기서는 간단히 검은색 이미지를 생성합니다.
width, height = 640, 480
img = cv2.imread('many_shape2.png') # 특정 이미지 파일 로드

if img is None:
    print("이미지를 로드할 수 없습니다. 파일 경로를 확인하거나 카메라가 연결되어 있는지 확인하세요.")
else:
    cv2.imshow('Image', img)  # 'Image'라는 이름의 창에 이미지 표시
    cv2.setMouseCallback('Image', mouse_callback)  # 'Image' 창에 마우스 콜백 함수 연결

    cv2.waitKey(0)  # 아무 키나 누를 때까지 대기
    cv2.destroyAllWindows() # 모든 창 닫기