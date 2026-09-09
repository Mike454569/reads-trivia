"""Content-quality exclusion list for CFB Rivalry Trivia (cfb_rivalry_trivia.py).

--- WHY THIS EXISTS ---
Real, measured problem in the curated `cfb_trivia_bank` rivalry packs (860
rows, `is_rivalry=1`, 43 real school-vs-school packs): roughly half of every
20-question pack is generic single-school identity trivia (school colors,
mascot name, fight song title, home stadium name, a player's national award
or NFL Draft slot, a coach's overall tenure) with a decorative clause tacked
on ("...part of a strong rivalry-era stretch", "...relevant to this
rivalry") that never actually tests any knowledge of the two schools
PLAYING EACH OTHER. A user playing "CFB Rivalries" reported this directly:
questions like "What are Auburn's school colors?" or "Which Wisconsin
running back won the Heisman in 1999" have nothing to do with the Iron Bowl
or the Axe rivalry as a competition -- they're just team facts wearing a
rivalry-pack label.

--- HOW THIS LIST WAS BUILT ---
Every one of the 860 `is_rivalry=1` rows was tested against one rule: does
the question text actually name BOTH of the pack's two real schools (via
`schools.school_name`, with a small alias map for 3 rows where the curated
text uses a casual name the `schools` table doesn't -- Pittsburgh/"Pitt",
South Florida/"USF", "Miami (FL)"/"Miami" -- and a same-prefix guard so
e.g. "Texas" doesn't false-match inside "Texas A&M") OR the specific named
rivalry itself (the trophy/nickname before the parenthetical in
`rivalry_pack_name`, e.g. "Iron Bowl", "Bedlam", "Paul Bunyan's Axe")?
Verified by direct manual reading of every flagged pack, not just the
automated pass (see CFBTRIV_1106-1272-range packs, Iowa/Iowa State, Penn
State/Pitt, UCLA/USC for the clearest examples of the pattern: colors x2 +
mascot x2 + fight song x2 + stadium name x2 + several individually-
notable-alum bios, all per pack, out of only 1-4 real head-to-head
rivalry facts each).

Second pass, caught in live production spot-checking after the first
458-row list shipped: 38 more rows still named the rivalry's nickname or
trophy only in a decorative aside ("...occasional Iron Bowl host", "...a
Paul Bunyan Trophy fixture") while the actual fact tested was still pure
single-school identity trivia (a stadium's name, a fight song title, a
conference a school joined) -- the name/nickname test alone isn't
sufficient when the nickname is name-dropped rather than the row's real
subject. These 38 are layered on top of the original 458 (496 total
excluded of 860; 364 real rivalry-specific rows remain).

This is a content-quality filter, not a data deletion -- the underlying
`cfb_trivia_bank` rows are untouched (they're real, correctly-written
questions, just not RIVALRY questions) and remain available to the general
CFB trivia categories they'd fit if ever re-tagged. See
`cfb_rivalry_trivia.py`'s `evaluate()` for how this list is applied.
"""
from __future__ import annotations

NON_RIVALRY_SPECIFIC_TRIVIA_IDS: frozenset[str] = frozenset(
    f"CFBTRIV_{n}"
    for n in (
        421, 425, 436, 438, 439, 442, 443, 444, 445, 446, 448, 450,
        452, 459, 460, 462, 463, 468, 469, 470, 475, 477, 478, 479,
        480, 481, 486, 488, 491, 492, 497, 498, 499, 501, 502, 503,
        510, 511, 512, 514, 516, 517, 518, 519, 522, 523, 525, 526,
        527, 529, 530, 531, 532, 534, 535, 536, 537, 538, 539, 540,
        541, 546, 547, 552, 555, 556, 557, 558, 562, 567, 568, 571,
        572, 574, 575, 578, 579, 580, 582, 583, 584, 588, 590, 591,
        601, 606, 609, 614, 616, 617, 618, 619, 620, 622, 626, 627,
        629, 630, 632, 634, 636, 637, 639, 640, 642, 644, 645, 649,
        650, 653, 655, 656, 657, 658, 659, 660, 661, 662, 663, 666,
        669, 672, 677, 678, 684, 690, 695, 696, 697, 698, 699, 700,
        701, 702, 703, 704, 705, 706, 707, 708, 710, 712, 714, 715,
        717, 718, 720, 723, 724, 730, 732, 737, 738, 740, 741, 745,
        746, 747, 756, 757, 760, 761, 762, 763, 764, 765, 766, 768,
        770, 774, 775, 776, 777, 778, 779, 780, 781, 782, 783, 784,
        785, 786, 787, 788, 790, 791, 793, 795, 796, 797, 802, 803,
        807, 810, 813, 814, 816, 817, 819, 820, 823, 826, 833, 834,
        835, 836, 837, 838, 839, 840, 842, 843, 844, 845, 847, 848,
        850, 851, 855, 856, 858, 859, 866, 867, 868, 871, 874, 876,
        877, 879, 882, 884, 885, 887, 888, 895, 896, 901, 902, 906,
        907, 908, 909, 911, 913, 915, 916, 919, 920, 925, 926, 929,
        930, 932, 933, 934, 935, 936, 937, 938, 939, 940, 941, 942,
        943, 944, 945, 946, 947, 948, 949, 951, 954, 956, 957, 961,
        962, 964, 965, 966, 967, 969, 972, 974, 975, 978, 979, 980,
        981, 984, 985, 986, 987, 988, 992, 994, 995, 996, 998, 999,
        1001, 1003, 1004, 1006, 1008, 1009, 1012, 1014, 1017, 1018, 1019, 1025,
        1027, 1029, 1031, 1033, 1034, 1035, 1036, 1037, 1040, 1041, 1042, 1043,
        1044, 1045, 1047, 1048, 1050, 1052, 1053, 1055, 1056, 1060, 1061, 1062,
        1064, 1069, 1073, 1074, 1079, 1082, 1084, 1085, 1089, 1090, 1091, 1093,
        1094, 1095, 1096, 1097, 1098, 1099, 1100, 1102, 1103, 1109, 1110, 1113,
        1114, 1115, 1116, 1117, 1118, 1124, 1125, 1127, 1128, 1129, 1130, 1136,
        1137, 1142, 1143, 1146, 1147, 1148, 1149, 1150, 1151, 1152, 1153, 1154,
        1155, 1156, 1157, 1158, 1159, 1160, 1161, 1162, 1163, 1165, 1167, 1168,
        1172, 1173, 1174, 1175, 1176, 1178, 1179, 1180, 1181, 1183, 1186, 1187,
        1189, 1191, 1192, 1194, 1195, 1196, 1201, 1202, 1203, 1204, 1205, 1206,
        1208, 1209, 1211, 1212, 1213, 1214, 1215, 1216, 1219, 1220, 1221, 1222,
        1223, 1225, 1226, 1228, 1229, 1230, 1232, 1233, 1234, 1238, 1239, 1240,
        1241, 1242, 1246, 1247, 1248, 1249, 1252, 1254, 1260, 1261, 1268, 1270,
        1271, 1272,
        # Second pass (see docstring): nickname/trophy name-dropped in an
        # aside, but the tested fact is still pure single-school identity.
        420, 428, 429, 587, 596, 597, 615, 631, 648, 681, 685, 719,
        729, 744, 799, 829, 849, 863, 886, 894, 899, 924, 963, 970,
        982, 1028, 1038, 1058, 1070, 1075, 1078, 1083, 1101, 1111, 1123, 1131,
        1171, 1218,
    )
)
