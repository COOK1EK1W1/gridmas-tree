
from cv2 import imread, subtract, imshow, waitKey, destroyAllWindows
import cv2

a = [(1366, 988), (1403, 952), (1404, 916), (1368, 877), (1407, 845), (1405, 804), (1391, 780), (1394, 720), (1376, 687), (1380, 648), (1363, 639), (1365, 628), (1365, 595), (1379, 605), (1426, 592), (1420, 646), (1653, 589), (1478, 678), (1490, 627), (1541, 666), (1556, 650), (1593, 631), (1602, 601), (1652, 595), (705, 454), (1674, 560), (1694, 545), (1670, 497), (1708, 485), (1693, 462), (1665, 438), (1610, 430), (1635, 473), (1607, 476), (1594, 512), (1593, 516), (1555, 554), (1548, 531), (1493, 556), (1471, 520), (1466, 502), (1499, 478), (1512, 427), (1505, 439), (1493, 392), (1530, 369), (1495, 368), (1456, 393), (1437, 358), (1397, 376), (1367, 387), (1389, 412), (1441, 428), (1427, 478), (1432, 473), (1409, 501), (1376, 527), (1353, 533), (1313, 513), (1294, 547), (1330, 571), (1331, 608), (1349, 624), (1347, 669), (1314, 712), (1315, 726), (1281, 742), (1247, 756), (1256, 695), (1204, 698), (1232, 665), (1224, 630), (1226, 617), (1246, 587), (1278, 566), (1257, 537), (1301, 512), (1271, 473), (1314, 448), (1305, 438), (1263, 420), (1228, 440), (1235, 439), (1226, 486), (1202, 491), (1174, 515), (1179, 538), (1172, 557), (1148, 546), (1126, 577), (1146, 610), (1111, 614), (1161, 621), (1127, 662), (1153, 704), (1107, 701), (1106, 718), (1086, 690), (1067, 724), (1041, 740), (962, 704), (965, 692), (988, 660), (1017, 634), (993, 590), (1038, 592), (1045, 546), (1062, 513), (1038, 487), (1077, 506), (1071, 468), (1092, 465), (1128, 450), (1106, 413), (1123, 394), (1107, 391), (1081, 346), (1056, 386), (1054, 382), (1035, 405), (1017, 370), (988, 378), (982, 389), (969, 424), (944, 415), (977, 406), (930, 382), (961, 368), (592, 427), (894, 357), (852, 350), (836, 332), (834, 379), (790, 359), (761, 386), (750, 369), (699, 387), (705, 385), (695, 385), (668, 408), (627, 379), (620, 378), (629, 379), (577, 394), (547, 394), (543, 362), (510, 381), (515, 395), (497, 400), (446, 368), (378, 403), (356, 383), (328, 390), (311, 372), (227, 363), (277, 348), (231, 353), (201, 373), (160, 356), (140, 345), (115, 382), (108, 408), (77, 444), (105, 470), (68, 490), (105, 508), (75, 549), (113, 582), (69, 591), (75, 634), (121, 662), (93, 691), (144, 749), (131, 750), (144, 752), (192, 755), (211, 808), (255, 817), (267, 846), (329, 820), (355, 858), (368, 848), (415, 831), (456, 807), (468, 779), (513, 764), (539, 808), (564, 787), (594, 769), (617, 793), (645, 768), (658, 774), (699, 786), (681, 816), (739, 806), (743, 853), (809, 840), (804, 870), (824, 867), (867, 834), (921, 753), (918, 725), (890, 696), (922, 653), (896, 648), (924, 590), (898, 587), (901, 555), (939, 534), (933, 480), (920, 459), (952, 436), (904, 458), (887, 443), (856, 447), (828, 437), (814, 403), (795, 443), (762, 452), (742, 430), (693, 446), (671, 411), (649, 404), (623, 450), (594, 437), (566, 437), (524, 420), (519, 443), (488, 445), (439, 458), (413, 451), (385, 431), (368, 425), (323, 428), (310, 409), (256, 395), (223, 414), (239, 440), (201, 469), (208, 503), (242, 590), (239, 571), (238, 588), (225, 634), (217, 688), (220, 691), (211, 688), (260, 727), (232, 747), (286, 761), (347, 678), (326, 682), (390, 638), (401, 634), (392, 617), (361, 566), (366, 540), (357, 534), (314, 501), (366, 495), (392, 543), (433, 522), (466, 501), (479, 492), (481, 488), (501, 526), (517, 547), (505, 565), (465, 581), (494, 618), (459, 630), (467, 668), (440, 699), (491, 686), (501, 620), (532, 641), (556, 661), (552, 622), (607, 606), (597, 570), (677, 495), (622, 545), (622, 497), (629, 495), (669, 470), (682, 490), (654, 537), (670, 556), (629, 576), (642, 607), (608, 632), (639, 646), (602, 688), (660, 700), (656, 729), (663, 722), (772, 671), (746, 701), (774, 669), (732, 676), (801, 696), (785, 664), (803, 616), (781, 585), (751, 597), (706, 597), (743, 615), (673, 616), (668, 588), (704, 581), (696, 573), (705, 525), (678, 489), (709, 458), (730, 484), (761, 475), (794, 463), (815, 508), (833, 456), (858, 485), (895, 491), (897, 499), (858, 506), (870, 561), (820, 575), (864, 586), (844, 635), (853, 660), (882, 679), (926, 674), (934, 707), (955, 671), (963, 668), (1011, 684), (1039, 684), (1067, 660), (1111, 658), (1133, 634), (1150, 632), (1145, 619), (1171, 601), (1175, 578), (1198, 567), (1214, 526), (1220, 526), (1249, 486), (1259, 491), (1268, 506), (1243, 528), (1272, 552)]

sumx = 0
minx = 2000
maxx = 0

minz = 0
maxz = 2000
for i in a:
    sumx += i[0]
    minx = min(minx, i[0])
    maxx = max(maxx, i[0])

    minz = max(minz, i[1])
    maxz = min(maxz, i[1])
mid = sumx / len(a)
print(minx, maxx, mid, minz, maxz)
for i in a:
    print(f"{((i[0] - mid) - minx) / (mid)}, 0, {(minz - i[1]) / (mid * 2)}")
exit()



imagedirs = [
    "results/results2-0-0.png",
    "results/results2-1-0.png",
    "results/results2-2-0.png",
    "results/results2-3-0.png",
    "results/results2-4-0.png",
    "results/results2-5-0.png",
    "results/results2-6-0.png",
    "results/results2-7-0.png",
    "results/results2-8-0.png",
]

cleanplate = "results/results2-9-0.png"
cleanimage = imread(cleanplate)

all = "results/results2-11-0.png"
circled = imread(all)
count = 0
allimage = subtract(imread(all), cleanimage)

images = map(lambda x: imread(x), imagedirs)

subtracted_images = list(map(lambda x: subtract(x, cleanimage), list(images)))

for pixelid in range(500):
    startimage = allimage
    for i, image in enumerate(subtracted_images):
        if (pixelid & 0x1 << i) == 0:
            startimage = subtract(startimage, image)
        else:
            startimage = subtract(startimage, subtract(allimage, image))

    gray = cv2.cvtColor(startimage, cv2.COLOR_BGR2GRAY)
    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(gray)
    if maxVal > 0:
        print(maxVal)
        cv2.circle(circled, maxLoc, 6, (255, 0, 0), 3)
        count += 1

print(count)
imshow("test", circled)
waitKey(0)
destroyAllWindows()
