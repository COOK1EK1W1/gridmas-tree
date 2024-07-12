import cv2

im0 = cv2.imread("scanning/results/results2-0-0.png")
im1 = cv2.imread("scanning/results/results2-1-0.png")
im2 = cv2.imread("scanning/results/results2-2-0.png")
im3 = cv2.imread("scanning/results/results2-3-0.png")
im4 = cv2.imread("scanning/results/results2-4-0.png")
im5 = cv2.imread("scanning/results/results2-5-0.png")
im6 = cv2.imread("scanning/results/results2-6-0.png")
im7 = cv2.imread("scanning/results/results2-7-0.png")
im8 = cv2.imread("scanning/results/results2-8-0.png")
im9 = cv2.imread("scanning/results/results2-9-0.png")

a0 = cv2.subtract(im0, im9)
a1 = cv2.subtract(im1, im9)
a2 = cv2.subtract(im2, im9)
a3 = cv2.subtract(im3, im9)
a4 = cv2.subtract(im4, im9)
a5 = cv2.subtract(im5, im9)
a6 = cv2.subtract(im6, im9)
a7 = cv2.subtract(im7, im9)
a8 = cv2.subtract(im8, im9)

comb = cv2.subtract(a0, a1)
comb = cv2.subtract(comb, a2)
comb = cv2.subtract(comb, a3)
comb = cv2.subtract(comb, a4)
comb = cv2.add(comb, a5)
comb = cv2.subtract(comb, a6)
comb = cv2.subtract(comb, a7)
comb = cv2.subtract(comb, a8)

cv2.imshow("test", comb)
cv2.waitKey(0)
cv2.destroyAllWindows()