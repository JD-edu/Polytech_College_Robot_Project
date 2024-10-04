import cv2
import numpy as np

img = cv2.imread("./image_single_obj.jpg")


img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
cv2.imshow('gray', img_gray)

_, img_bin = cv2.threshold(img_gray, 50, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

cv2.imshow('bin', img_bin)

contours, _ = cv2.findContours(img_bin, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

for i, cont in enumerate(contours):
    
    area = cv2.contourArea(cont)
    if area > 18000 and area < 100000:
        cv2.drawContours(img, contours, i, (0,0,255), 2)
        cv2.imshow('original', img)
       
        # get orientation 
        size_of_cont = len(cont)
        data_of_point = np.empty((size_of_cont, 2), dtype=np.float64)
        
        ''' Contour is list. Shape example is as follwings.
        [[[108  22]]
        [[107  23]]
        [[106  23]]
        ...

        [[111  22]]
        [[110  22]]
        [[109  22]]]
        '''
        for i in range(data_of_point.shape[0]):
            data_of_point[i][0] = cont[i][0][0]
            data_of_point[i][1] = cont[i][0][1]

        mean = np.empty((0))
        mean, eigenvectors, eigenvalues = cv2.PCACompute2(data_of_point, mean)
        print(eigenvectors)
        print(eigenvalues)
        
     
cv2.waitKey(0)

cv2.destroyAllWindows()