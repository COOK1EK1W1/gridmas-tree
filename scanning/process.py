import cv2
lol = []
for i in range(50):
    img = cv2.imread(f'scanning/results/results-{i}.png')
    gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(gray_image)

    brightest_point = maxLoc

    print(f"The brightest point in the image is at: {brightest_point}")
    cv2.circle(img, maxLoc, 5, (255, 0, 0), 1)
    lol.append(maxLoc)

    cv2.imshow('image', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

print(lol)
