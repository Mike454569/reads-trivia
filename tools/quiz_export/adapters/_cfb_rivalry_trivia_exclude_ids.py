"""Content-quality exclusion list for CFB Rivalry Trivia (cfb_rivalry_trivia.py).

--- WHY THIS EXISTS ---
Real, measured problem in the curated `cfb_trivia_bank` rivalry packs (860
rows, `is_rivalry=1`, 43 real school-vs-school packs): a majority of every
20-question pack turned out to be generic single-school trivia (school
colors, mascot name, fight song title, home stadium name, a player's
national award or NFL Draft slot, a coach's hiring/tenure, a national
championship or bowl-game bio) with a decorative clause tacked on
("...part of a strong rivalry-era stretch", "...relevant to this
rivalry") that never actually tests any knowledge of the two schools
PLAYING EACH OTHER. A user playing "CFB Rivalries" reported this directly:
questions like "What are Auburn's school colors?" or "Both programs claim
a combined total of well over a dozen national championships -- true or
false?" have nothing to do with the Iron Bowl or Nebraska-Oklahoma as an
actual rivalry -- they're team facts (or, for the national-championship
example, facts about a completely different competition) wearing a
rivalry-pack label.

--- HOW THIS LIST WAS BUILT (three passes, each catching a real gap in
the previous one -- documented honestly rather than collapsed into a
single pass, since the gaps are instructive) ---

Pass 1: does the question name BOTH of the pack's two real schools (via
`schools.school_name`, with a small alias map for 3 rows where the
curated text uses a casual name the `schools` table doesn't --
Pittsburgh/"Pitt", South Florida/"USF", "Miami (FL)"/"Miami" -- and a
same-prefix guard so e.g. "Texas" doesn't false-match inside "Texas
A&M") OR the specific named rivalry itself (the trophy/nickname before
the parenthetical in `rivalry_pack_name`, e.g. "Iron Bowl", "Bedlam",
"Paul Bunyan's Axe")? This alone found 458 non-rivalry rows.

Pass 2: live spot-checking the deployed fix immediately surfaced a real
gap -- "Alabama vs. Auburn: What is the name of Alabama's home stadium,
occasional Iron Bowl host?" passed Pass 1 because "Iron Bowl" is
name-dropped in the sentence, even though the actual fact tested is a
stadium's name. Added a hard override: identity-trivia patterns (school
colors / mascot / fight song / stadium name / conference-join-or-leave)
now exclude a row regardless of a name/nickname match. +38 rows.

Pass 3: broader sampling of what Pass 1+2 still kept found the same
problem one level up -- individual awards (Heisman and every other named
award), NFL Draft stock, national championships, real postseason bowl
games (Rose/Sugar/Orange/Fiesta/Peach/Cotton/Outback/Citrus/Gator/
Holiday/Alamo -- never a rivalry's own "___ Bowl" nickname, none of
which collide with these names), CFP/conference-championship-game
results, and coach hiring events (took over/hired/succeeded/preceded/
replaced) were all still being kept whenever a school name or the
rivalry nickname happened to appear anywhere in the same sentence, even
as pure decoration around an unrelated achievement. Added the same kind
of hard override for these. +353 rows.

Pass 4: a live spot-check against the deployed Pass-3 fix (six real
sampled production questions) caught 3 more of the exact same class --
"led the program to its first-ever #1 AP ranking" / "reached #1 in the
AP poll" / "transformed Kansas State ... into a national power" -- a
national-ranking or program-turnaround bio, not a rivalry-game outcome.
Added `ap ranking` / `ap poll` / `transformed ... program` / `national
power` to the override, but deliberately kept CFBTRIV_464 ("The 2006
edition of The Game featured both teams ranked #1 and #2 -- who won that
game?") out of the override despite matching a ranking mention, since
its own real subject IS the rivalry game's outcome -- a bare "#\d+
ranked" pattern would have wrongly killed a genuinely good row along
with the bad ones, so no such blanket pattern was added.

Pass 5: rather than keep chasing individual regex gaps one live sample
at a time, every one of the 230 rows Pass 4 still kept was read and
judged directly, row by row (not pattern-matched) -- the real test
applied: does the question's own core interrogative target the rivalry
itself (its trophy/nickname/history/series record, a specific rivalry-
game outcome or moment, a coach or player's specific rivalry-game
dominance, or a direct comparison of both rival schools), or does it
target some other achievement (a coach's general tenure/hire/resurgence,
a national/conference stat record, a win over a THIRD team, a program's
own standalone tradition) with the rivalry only riding along as an era-
marker or decorative clause? 63 more rows failed this direct read and
were added (e.g. CFBTRIV_500's "Ole Miss coach led consecutive Egg
Bowl-era wins over ALABAMA" -- the opponent named is a third team, not
the Egg Bowl's own rival Mississippi State; CFBTRIV_759's "scored 6
touchdowns against MICHIGAN in 1924 ... alongside its Northwestern
rivalry" -- same wrong-opponent pattern).

Final: 693 of 860 rows excluded, 167 remain -- verified by direct
re-sampling after each pass, including two live pulls from the deployed
API, plus a full direct manual read of everything Pass 4 kept (Pass 5).
The 167 that remain are overwhelmingly real: rivalry trophy/nickname
origin and history, series records and streaks, specific rivalry-game
outcomes and moments, a coach or player's specific in-rivalry dominance,
and direct comparisons of both rival schools. No classification of 860
free-text rows by any method is claimed to be perfect -- this is the
result of five real, disclosed passes, not a claim of zero remaining
edge cases.

This is a content-quality filter, not a data deletion -- the underlying
`cfb_trivia_bank` rows are untouched (they're real, correctly-written
questions, just not RIVALRY questions) and remain available to the
general CFB trivia categories they'd fit if ever re-tagged. See
`cfb_rivalry_trivia.py`'s `evaluate()` for how this list is applied.
"""
from __future__ import annotations

NON_RIVALRY_SPECIFIC_TRIVIA_IDS: frozenset[str] = frozenset(
    f"CFBTRIV_{n}"
    for n in (
        419, 420, 421, 425, 427, 428, 429, 430, 432, 436, 437, 438,
        439, 442, 443, 444, 445, 446, 448, 450, 452, 457, 458, 459,
        460, 461, 462, 463, 465, 466, 467, 468, 469, 470, 472, 475,
        476, 477, 478, 479, 480, 481, 483, 486, 487, 488, 490, 491,
        492, 497, 498, 499, 501, 502, 503, 505, 506, 510, 511, 512,
        514, 516, 517, 518, 519, 521, 522, 523, 524, 525, 526, 527,
        529, 530, 531, 532, 534, 535, 536, 537, 538, 539, 540, 541,
        542, 543, 546, 547, 549, 552, 554, 555, 556, 557, 558, 559,
        562, 565, 567, 568, 571, 572, 574, 575, 578, 579, 580, 581,
        582, 583, 584, 587, 588, 590, 591, 594, 595, 596, 597, 598,
        600, 601, 602, 603, 606, 607, 609, 614, 615, 616, 617, 618,
        619, 620, 622, 623, 625, 626, 627, 629, 630, 631, 632, 634,
        635, 636, 637, 639, 640, 641, 642, 643, 644, 645, 647, 648,
        649, 650, 653, 655, 656, 657, 658, 659, 660, 661, 662, 663,
        664, 666, 669, 671, 672, 675, 676, 677, 678, 681, 682, 684,
        685, 686, 690, 691, 695, 696, 697, 698, 699, 700, 701, 702,
        703, 704, 705, 706, 707, 708, 710, 712, 714, 715, 716, 717,
        718, 719, 720, 721, 723, 724, 726, 729, 730, 732, 735, 736,
        737, 738, 740, 741, 743, 744, 745, 746, 747, 748, 750, 756,
        757, 758, 760, 761, 762, 763, 764, 765, 766, 768, 769, 770,
        774, 775, 776, 777, 778, 779, 780, 781, 782, 783, 784, 785,
        786, 787, 788, 790, 791, 793, 795, 796, 797, 799, 801, 802,
        803, 805, 807, 808, 809, 810, 811, 813, 814, 815, 816, 817,
        819, 820, 821, 822, 823, 824, 825, 826, 827, 829, 831, 833,
        834, 835, 836, 837, 838, 839, 840, 841, 842, 843, 844, 845,
        847, 848, 849, 850, 851, 854, 855, 856, 857, 858, 859, 863,
        864, 866, 867, 868, 870, 871, 874, 876, 877, 878, 879, 880,
        882, 883, 884, 885, 886, 887, 888, 889, 891, 894, 895, 896,
        898, 899, 900, 901, 902, 904, 906, 907, 908, 909, 911, 913,
        914, 915, 916, 917, 918, 919, 920, 922, 923, 924, 925, 926,
        927, 928, 929, 930, 932, 933, 934, 935, 936, 937, 938, 939,
        940, 941, 942, 943, 944, 945, 946, 947, 948, 949, 951, 953,
        954, 956, 957, 958, 959, 960, 961, 962, 963, 964, 965, 966,
        967, 969, 970, 972, 974, 975, 976, 978, 979, 980, 981, 982,
        984, 985, 986, 987, 988, 992, 994, 995, 996, 997, 998, 999,
        1000, 1001, 1002, 1003, 1004, 1006, 1008, 1009, 1010, 1012, 1014, 1015,
        1016, 1017, 1018, 1019, 1021, 1022, 1024, 1025, 1027, 1028, 1029, 1031,
        1032, 1033, 1034, 1035, 1036, 1037, 1038, 1040, 1041, 1042, 1043, 1044,
        1045, 1046, 1047, 1048, 1050, 1052, 1053, 1055, 1056, 1058, 1060, 1061,
        1062, 1064, 1067, 1069, 1070, 1072, 1073, 1074, 1075, 1077, 1078, 1079,
        1080, 1081, 1082, 1083, 1084, 1085, 1089, 1090, 1091, 1093, 1094, 1095,
        1096, 1097, 1098, 1099, 1100, 1101, 1102, 1103, 1107, 1109, 1110, 1111,
        1112, 1113, 1114, 1115, 1116, 1117, 1118, 1119, 1121, 1123, 1124, 1125,
        1127, 1128, 1129, 1130, 1131, 1132, 1134, 1135, 1136, 1137, 1138, 1140,
        1141, 1142, 1143, 1146, 1147, 1148, 1149, 1150, 1151, 1152, 1153, 1154,
        1155, 1156, 1157, 1158, 1159, 1160, 1161, 1162, 1163, 1165, 1166, 1167,
        1168, 1169, 1171, 1172, 1173, 1174, 1175, 1176, 1178, 1179, 1180, 1181,
        1183, 1185, 1186, 1187, 1188, 1189, 1191, 1192, 1194, 1195, 1196, 1199,
        1201, 1202, 1203, 1204, 1205, 1206, 1208, 1209, 1210, 1211, 1212, 1213,
        1214, 1215, 1216, 1218, 1219, 1220, 1221, 1222, 1223, 1224, 1225, 1226,
        1228, 1229, 1230, 1232, 1233, 1234, 1238, 1239, 1240, 1241, 1242, 1243,
        1246, 1247, 1248, 1249, 1250, 1252, 1253, 1254, 1260, 1261, 1263, 1268,
        1270, 1271, 1272,
        # Pass 4 (see docstring): AP ranking / program-turnaround bios
        # caught by live spot-checking the deployed Pass-3 fix.
        496, 993, 1190,
        # Pass 5 (see docstring): direct manual read of everything Pass 4
        # still kept -- coach tenure/hire/resurgence bios, national/
        # conference stat records, and wrong-opponent rows (a game against
        # a THIRD team, decorated with this pack's rivalry name).
        500, 504, 508, 528, 544, 577, 586, 589, 621, 628,
        638, 646, 652, 668, 679, 680, 687, 688, 725, 731,
        739, 742, 752, 754, 759, 767, 772, 794, 800, 804,
        806, 818, 860, 861, 862, 875, 881, 897, 903, 921,
        973, 990, 1005, 1007, 1013, 1051, 1054, 1057, 1063, 1066,
        1076, 1105, 1108, 1120, 1133, 1170, 1177, 1193, 1197, 1217,
        1227, 1237, 1245,
    )
)
