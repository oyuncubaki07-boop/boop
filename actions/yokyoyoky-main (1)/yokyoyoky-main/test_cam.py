import cv2
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Kamera açılamadı!")
else:
    ret, frame = cap.read()
    if ret:
        cv2.imshow("Test", frame)
        cv2.waitKey(2000)
        cv2.destroyAllWindows()
    else:
        print("Görüntü alınamadı")
cap.release()