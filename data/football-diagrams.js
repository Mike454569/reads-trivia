// Football 101 Interactive Redesign: data-driven formation/front/coverage/
// concept diagram library, consumed by football-field.js's single reusable
// SVG renderer. Generated -- do not hand-edit; re-run
// `python3 -m tools.learn.build_football_diagrams` after changing
// tools/learn/build_football_diagrams.py.
//
// Every top-level key here is the exact canonical_id LEARN_ENCYCLOPEDIA.
// concepts already uses (data/learn-encyclopedia.js), so a diagram attaches
// to a real, existing encyclopedia concept instead of forking a parallel
// content system -- except entries marked verified:false, which have no
// matching source-verified concept yet and are labeled as diagram-only
// references in the UI rather than borrowing a false verified badge.
window.FOOTBALL_DIAGRAMS = {
 "formations": {
  "FORMATION_I_FORMATION": {
   "id": "FORMATION_I_FORMATION",
   "side": "offense",
   "los_y": 50,
   "category": "formation",
   "verified": true,
   "display_name": "I-Formation",
   "personnel": "21",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "TE",
     "label": "TE",
     "x": 76,
     "y": 50,
     "role": "Tight End",
     "position_ref": "POSITION_TIGHT_END_Y",
     "assignment": "In-line blocker or short/intermediate receiving option."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 54,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "FB",
     "label": "FB",
     "x": 50,
     "y": 60,
     "role": "Fullback",
     "position_ref": "POSITION_FULLBACK",
     "assignment": "Lead blocker; occasional short-yardage carrier."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 50,
     "y": 68,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "WR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "role": "Z Receiver",
     "position_ref": "POSITION_Z_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    }
   ],
   "notes": "Fullback and running back stack directly behind the quarterback -- the classic downhill run-first look.",
   "description": "I-Formation: fullback and tailback stacked behind an under-center quarterback, one tight end, two wide receivers."
  },
  "FORMATION_STRONG_I_WEAK_I": {
   "id": "FORMATION_STRONG_I_WEAK_I",
   "side": "offense",
   "los_y": 50,
   "category": "formation",
   "verified": true,
   "display_name": "Strong I / Weak I",
   "personnel": "21",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "TE",
     "label": "TE",
     "x": 76,
     "y": 50,
     "role": "Tight End",
     "position_ref": "POSITION_TIGHT_END_Y",
     "assignment": "In-line blocker or short/intermediate receiving option."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 54,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "FB",
     "label": "FB",
     "x": 58,
     "y": 59,
     "role": "Fullback",
     "position_ref": "POSITION_FULLBACK",
     "assignment": "Lead blocker; occasional short-yardage carrier."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 50,
     "y": 68,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "WR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "role": "Z Receiver",
     "position_ref": "POSITION_Z_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    }
   ],
   "notes": "Same base I-Formation with the fullback offset toward (Strong I) or away from (Weak I) the tight end -- shown here offset strong-side; mirror the fullback to the opposite guard for Weak I.",
   "variation_note": "Playbooks differ on whether \"strong\" is named for the tight end or the fullback's offset -- confirm the rule your source uses.",
   "description": "Strong I: fullback offset toward the tight end / strength call, tailback still deep behind the quarterback."
  },
  "FORMATION_SINGLEBACK_ACE": {
   "id": "FORMATION_SINGLEBACK_ACE",
   "side": "offense",
   "los_y": 50,
   "category": "formation",
   "verified": true,
   "display_name": "Singleback / Ace",
   "personnel": "11",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "TE",
     "label": "TE",
     "x": 76,
     "y": 50,
     "role": "Tight End",
     "position_ref": "POSITION_TIGHT_END_Y",
     "assignment": "In-line blocker or short/intermediate receiving option."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 54,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 44,
     "y": 66,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "WR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "role": "Z Receiver",
     "position_ref": "POSITION_Z_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "SL1",
     "label": "SL",
     "x": 84,
     "y": 48,
     "role": "Slot / F Receiver",
     "position_ref": "POSITION_SLOT_F_RECEIVER",
     "assignment": "Works the middle of the field; frequent option/RPO read."
    }
   ],
   "notes": "One deep back, no fullback -- releases a fourth or fifth eligible receiver while keeping downhill run action.",
   "description": "Singleback/Ace: one running back behind an under-center quarterback, balanced receiver split, no fullback."
  },
  "FORMATION_PISTOL": {
   "id": "FORMATION_PISTOL",
   "side": "offense",
   "los_y": 50,
   "category": "formation",
   "verified": true,
   "display_name": "Pistol",
   "personnel": "11",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "TE",
     "label": "TE",
     "x": 76,
     "y": 50,
     "role": "Tight End",
     "position_ref": "POSITION_TIGHT_END_Y",
     "assignment": "In-line blocker or short/intermediate receiving option."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 58,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 50,
     "y": 65,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "WR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "role": "Z Receiver",
     "position_ref": "POSITION_Z_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "SL1",
     "label": "SL",
     "x": 20,
     "y": 48,
     "role": "Slot / F Receiver",
     "position_ref": "POSITION_SLOT_F_RECEIVER",
     "assignment": "Works the middle of the field; frequent option/RPO read."
    }
   ],
   "notes": "Quarterback lines up shallower than shotgun with the back directly behind him -- keeps shotgun spacing while preserving a downhill run track.",
   "description": "Pistol: quarterback a few yards behind center with the running back stacked directly behind him."
  },
  "FORMATION_SHOTGUN": {
   "id": "FORMATION_SHOTGUN",
   "side": "offense",
   "los_y": 50,
   "category": "formation",
   "verified": true,
   "display_name": "Shotgun",
   "personnel": "11",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "TE",
     "label": "TE",
     "x": 76,
     "y": 50,
     "role": "Tight End",
     "position_ref": "POSITION_TIGHT_END_Y",
     "assignment": "In-line blocker or short/intermediate receiving option."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 63,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 40,
     "y": 62,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "WR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "role": "Z Receiver",
     "position_ref": "POSITION_Z_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "SL1",
     "label": "SL",
     "x": 84,
     "y": 48,
     "role": "Slot / F Receiver",
     "position_ref": "POSITION_SLOT_F_RECEIVER",
     "assignment": "Works the middle of the field; frequent option/RPO read."
    }
   ],
   "notes": "Quarterback aligns several yards behind center. \"Gun\" describes the QB's depth, not a complete formation -- back alignment and receiver splits still vary play to play.",
   "description": "Shotgun: quarterback several yards deep, running back offset to one side, one tight end, two outside receivers plus a slot."
  },
  "FORMATION_3X1_TRIPS": {
   "id": "FORMATION_3X1_TRIPS",
   "side": "offense",
   "los_y": 50,
   "category": "formation",
   "verified": true,
   "display_name": "Trips (3x1)",
   "personnel": "11",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 28,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 37,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 46,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 55,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 64,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 46,
     "y": 63,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 38,
     "y": 62,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 8,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "WR2",
     "label": "WR",
     "x": 92,
     "y": 50,
     "role": "Z Receiver",
     "position_ref": "POSITION_Z_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "SL1",
     "label": "SL",
     "x": 80,
     "y": 48,
     "role": "Slot / F Receiver",
     "position_ref": "POSITION_SLOT_F_RECEIVER",
     "assignment": "Works the middle of the field; frequent option/RPO read."
    },
    {
     "id": "SL2",
     "label": "SL",
     "x": 68,
     "y": 46,
     "role": "Slot / F Receiver",
     "position_ref": "POSITION_SLOT_F_RECEIVER",
     "assignment": "Works the middle of the field; frequent option/RPO read."
    }
   ],
   "notes": "Three eligible receivers stacked to one side (the \"trips\" side), one isolated receiver on the backside -- shown here out of shotgun (\"Shotgun Trips\" is this same alignment with the QB in the gun, as drawn).",
   "variation_note": "Trips can be run under center or from shotgun/pistol -- the receiver-side numbers advantage is the defining feature, not the QB depth.",
   "description": "Trips: three receivers bunched to one side of the formation, one receiver isolated on the backside, quarterback in shotgun."
  },
  "FORMATION_BUNCH": {
   "id": "FORMATION_BUNCH",
   "side": "offense",
   "los_y": 50,
   "category": "formation",
   "verified": true,
   "display_name": "Bunch",
   "personnel": "11",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 63,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 40,
     "y": 62,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 8,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "WR2",
     "label": "WR",
     "x": 88,
     "y": 50,
     "role": "Z Receiver",
     "position_ref": "POSITION_Z_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "SL1",
     "label": "SL",
     "x": 80,
     "y": 47,
     "role": "Slot / F Receiver",
     "position_ref": "POSITION_SLOT_F_RECEIVER",
     "assignment": "Works the middle of the field; frequent option/RPO read."
    },
    {
     "id": "SL2",
     "label": "SL",
     "x": 84,
     "y": 44,
     "role": "Slot / F Receiver",
     "position_ref": "POSITION_SLOT_F_RECEIVER",
     "assignment": "Works the middle of the field; frequent option/RPO read."
    }
   ],
   "notes": "Three receivers tightly clustered pre-snap (not spread across the formation) to create natural rub/pick leverage against man coverage.",
   "description": "Bunch: three receivers clustered tightly together to one side, creating natural picks against man coverage."
  },
  "FORMATION_EMPTY": {
   "id": "FORMATION_EMPTY",
   "side": "offense",
   "los_y": 50,
   "category": "formation",
   "verified": true,
   "display_name": "Empty",
   "personnel": "10",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 63,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 4,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "WR2",
     "label": "WR",
     "x": 96,
     "y": 50,
     "role": "Z Receiver",
     "position_ref": "POSITION_Z_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "SL1",
     "label": "SL",
     "x": 16,
     "y": 48,
     "role": "Slot / F Receiver",
     "position_ref": "POSITION_SLOT_F_RECEIVER",
     "assignment": "Works the middle of the field; frequent option/RPO read."
    },
    {
     "id": "SL2",
     "label": "SL",
     "x": 84,
     "y": 48,
     "role": "Slot / F Receiver",
     "position_ref": "POSITION_SLOT_F_RECEIVER",
     "assignment": "Works the middle of the field; frequent option/RPO read."
    },
    {
     "id": "SL3",
     "label": "SL",
     "x": 68,
     "y": 46,
     "role": "Slot / F Receiver",
     "position_ref": "POSITION_SLOT_F_RECEIVER",
     "assignment": "Works the middle of the field; frequent option/RPO read."
    }
   ],
   "notes": "No running back stays in to block -- all five eligible receivers release, and the quarterback works entirely from the gun.",
   "description": "Empty: no running back in the backfield, five eligible receivers spread across the formation, quarterback alone in shotgun."
  },
  "FORMATION_PRO_SET_SPLIT_BACKS": {
   "id": "FORMATION_PRO_SET_SPLIT_BACKS",
   "side": "offense",
   "los_y": 50,
   "category": "formation",
   "verified": true,
   "display_name": "Pro Set (Split Backs)",
   "personnel": "21",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "TE",
     "label": "TE",
     "x": 76,
     "y": 50,
     "role": "Tight End",
     "position_ref": "POSITION_TIGHT_END_Y",
     "assignment": "In-line blocker or short/intermediate receiving option."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 54,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB1",
     "label": "RB",
     "x": 40,
     "y": 60,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "RB2",
     "label": "RB",
     "x": 60,
     "y": 60,
     "role": "Fullback",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "WR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "role": "Z Receiver",
     "position_ref": "POSITION_Z_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    }
   ],
   "notes": "Two backs aligned side by side rather than stacked -- balanced protection and misdirection options in both directions.",
   "description": "Pro Set: two running backs split side by side behind an under-center quarterback, one tight end, two wide receivers."
  },
  "FORMATION_WISHBONE": {
   "id": "FORMATION_WISHBONE",
   "side": "offense",
   "los_y": 50,
   "category": "formation",
   "verified": true,
   "display_name": "Wishbone",
   "personnel": "30",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "TE",
     "label": "TE",
     "x": 76,
     "y": 50,
     "role": "Tight End",
     "position_ref": "POSITION_TIGHT_END_Y",
     "assignment": "In-line blocker or short/intermediate receiving option."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 54,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "FB",
     "label": "FB",
     "x": 50,
     "y": 59,
     "role": "Fullback",
     "position_ref": "POSITION_FULLBACK",
     "assignment": "Lead blocker; occasional short-yardage carrier."
    },
    {
     "id": "RB1",
     "label": "RB",
     "x": 40,
     "y": 65,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "RB2",
     "label": "RB",
     "x": 60,
     "y": 65,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 8,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "WR2",
     "label": "WR",
     "x": 92,
     "y": 50,
     "role": "Z Receiver",
     "position_ref": "POSITION_Z_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    }
   ],
   "notes": "Triple-option base: fullback stacked behind the QB, two halfbacks split behind and outside him, forming a Y/wishbone shape.",
   "description": "Wishbone: three running backs arranged in a Y behind an under-center quarterback -- a run-heavy triple-option base."
  },
  "FORMATION_FLEXBONE": {
   "id": "FORMATION_FLEXBONE",
   "side": "offense",
   "los_y": 50,
   "category": "formation",
   "verified": true,
   "display_name": "Flexbone",
   "personnel": "20",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 54,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "FB",
     "label": "FB",
     "x": 50,
     "y": 59,
     "role": "Fullback",
     "position_ref": "POSITION_FULLBACK",
     "assignment": "Lead blocker; occasional short-yardage carrier."
    },
    {
     "id": "RB1",
     "label": "RB",
     "x": 26,
     "y": 58,
     "role": "Slotback",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "RB2",
     "label": "RB",
     "x": 74,
     "y": 58,
     "role": "Slotback",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "WR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "role": "Z Receiver",
     "position_ref": "POSITION_Z_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    }
   ],
   "notes": "Modern triple-option variant: the wishbone's halfbacks move up and out into slot alignments (\"slotbacks\") just off the line.",
   "description": "Flexbone: a fullback behind the quarterback with two slotbacks aligned just outside the tackles -- the modern triple-option base."
  },
  "FORMATION_MARYLAND_I_POWER_I": {
   "id": "FORMATION_MARYLAND_I_POWER_I",
   "side": "offense",
   "los_y": 50,
   "category": "formation",
   "verified": true,
   "display_name": "Power I",
   "personnel": "22",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "TE",
     "label": "TE",
     "x": 76,
     "y": 50,
     "role": "Tight End",
     "position_ref": "POSITION_TIGHT_END_Y",
     "assignment": "In-line blocker or short/intermediate receiving option."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 54,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "FB",
     "label": "FB",
     "x": 50,
     "y": 58,
     "role": "Fullback",
     "position_ref": "POSITION_FULLBACK",
     "assignment": "Lead blocker; occasional short-yardage carrier."
    },
    {
     "id": "FB2",
     "label": "RB",
     "x": 58,
     "y": 59,
     "role": "Fullback",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 50,
     "y": 67,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 8,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    }
   ],
   "notes": "Adds a second lead blocker (two fullbacks/H-backs) in front of the tailback for maximum downhill push -- a heavy short-yardage/goal-line personnel package.",
   "description": "Power I: two lead blockers stacked in front of the tailback behind an under-center quarterback -- a heavy short-yardage package."
  },
  "SYSTEM_SPREAD_OPTION": {
   "id": "SYSTEM_SPREAD_OPTION",
   "side": "offense",
   "los_y": 50,
   "category": "formation",
   "verified": true,
   "display_name": "Spread",
   "personnel": "10/11",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 63,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 42,
     "y": 62,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 4,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "WR2",
     "label": "WR",
     "x": 96,
     "y": 50,
     "role": "Z Receiver",
     "position_ref": "POSITION_Z_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "SL1",
     "label": "SL",
     "x": 18,
     "y": 48,
     "role": "Slot / F Receiver",
     "position_ref": "POSITION_SLOT_F_RECEIVER",
     "assignment": "Works the middle of the field; frequent option/RPO read."
    },
    {
     "id": "SL2",
     "label": "SL",
     "x": 82,
     "y": 48,
     "role": "Slot / F Receiver",
     "position_ref": "POSITION_SLOT_F_RECEIVER",
     "assignment": "Works the middle of the field; frequent option/RPO read."
    }
   ],
   "notes": "\"Spread\" is a philosophy -- widening the formation to create space and simplify reads -- not one single fixed alignment. This shows a common 2x2 shotgun base; a spread offense may run Empty, Trips, or a dozen other actual formations from the same philosophy.",
   "variation_note": "Every team's version of \"spread\" looks different -- some run almost exclusively from 2x2, others live in 3x1/Trips or Empty. Treat this diagram as one representative look, not the definition.",
   "description": "Spread: offense widened into a 2x2 shotgun look to create space -- one representative alignment of a broader spread philosophy."
  },
  "DIAGRAM_WING_T": {
   "id": "DIAGRAM_WING_T",
   "side": "offense",
   "los_y": 50,
   "category": "formation",
   "verified": false,
   "display_name": "Wing-T",
   "personnel": "21",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "TE",
     "label": "TE",
     "x": 76,
     "y": 50,
     "role": "Tight End",
     "position_ref": "POSITION_TIGHT_END_Y",
     "assignment": "In-line blocker or short/intermediate receiving option."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 54,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "FB",
     "label": "FB",
     "x": 50,
     "y": 58,
     "role": "Fullback",
     "position_ref": "POSITION_FULLBACK",
     "assignment": "Lead blocker; occasional short-yardage carrier."
    },
    {
     "id": "HB",
     "label": "RB",
     "x": 62,
     "y": 59,
     "role": "Halfback",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WING",
     "label": "WG",
     "x": 82,
     "y": 50,
     "role": "Wingback",
     "position_ref": "POSITION_SLOT_F_RECEIVER",
     "assignment": "Tight to the formation, just outside the tight end -- misdirection and counter-action keys off his motion."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    }
   ],
   "notes": "A wingback aligns just outside the tight end. Built around misdirection (buck sweep, counters, waggle) rather than one fixed alignment -- not yet a dedicated entry in the source encyclopedia, so this is a diagram reference only.",
   "description": "Wing-T: a wingback tight outside the tight end, fullback and halfback in the backfield -- a misdirection-heavy run scheme."
  }
 },
 "fronts": {
  "FRONT_BASE_4_3": {
   "id": "FRONT_BASE_4_3",
   "side": "defense",
   "los_y": 50,
   "category": "front",
   "verified": true,
   "display_name": "4-3",
   "personnel": "4 DL / 3 LB / 4 DB",
   "players": [
    {
     "id": "LE",
     "label": "LE",
     "x": 36,
     "y": 48,
     "role": "Left Defensive End",
     "position_ref": "POSITION_DEFENSIVE_END",
     "assignment": "Sets the edge; contain rusher."
    },
    {
     "id": "DT1",
     "label": "DT",
     "x": 45,
     "y": 48,
     "role": "3-Technique",
     "position_ref": "POSITION_3_TECHNIQUE",
     "assignment": "Attacks the outside shoulder of the guard."
    },
    {
     "id": "DT2",
     "label": "NT",
     "x": 55,
     "y": 48,
     "role": "Nose Tackle",
     "position_ref": "POSITION_NOSE_TACKLE",
     "assignment": "Occupies the center; anchors the interior."
    },
    {
     "id": "RE",
     "label": "RE",
     "x": 64,
     "y": 48,
     "role": "Right Defensive End",
     "position_ref": "POSITION_DEFENSIVE_END",
     "assignment": "Sets the edge; contain rusher."
    },
    {
     "id": "WLB",
     "label": "W",
     "x": 30,
     "y": 38,
     "role": "Will Linebacker",
     "position_ref": "POSITION_WILL_LINEBACKER",
     "assignment": "Weak-side run fit and coverage."
    },
    {
     "id": "MLB",
     "label": "M",
     "x": 50,
     "y": 36,
     "role": "Mike Linebacker",
     "position_ref": "POSITION_MIKE_LINEBACKER",
     "assignment": "Makes the defensive call; downhill run fit."
    },
    {
     "id": "SLB",
     "label": "S",
     "x": 70,
     "y": 38,
     "role": "Sam Linebacker",
     "position_ref": "POSITION_SAM_LINEBACKER",
     "assignment": "Strong-side run fit, often vs. the tight end."
    },
    {
     "id": "CB1",
     "label": "CB",
     "x": 8,
     "y": 42,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Outside coverage leverage."
    },
    {
     "id": "CB2",
     "label": "CB",
     "x": 92,
     "y": 42,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Outside coverage leverage."
    },
    {
     "id": "FS",
     "label": "FS",
     "x": 38,
     "y": 18,
     "role": "Free Safety",
     "position_ref": "POSITION_FREE_SAFETY",
     "assignment": "Deep help; last line vs. the pass."
    },
    {
     "id": "SS",
     "label": "SS",
     "x": 62,
     "y": 20,
     "role": "Strong Safety",
     "position_ref": "POSITION_STRONG_SAFETY",
     "assignment": "Run support and coverage vs. the tight end/slot."
    }
   ],
   "notes": "Four down linemen, three linebackers -- the most common base front in modern football. Coverage shell shown here is neutral two-high; the front is called independently of the coverage behind it.",
   "description": "4-3: four down linemen, three linebackers, four defensive backs."
  },
  "FRONT_BASE_3_4": {
   "id": "FRONT_BASE_3_4",
   "side": "defense",
   "los_y": 50,
   "category": "front",
   "verified": true,
   "display_name": "3-4",
   "personnel": "3 DL / 4 LB / 4 DB",
   "players": [
    {
     "id": "DE1",
     "label": "DE",
     "x": 38,
     "y": 48,
     "role": "Defensive End",
     "position_ref": "POSITION_DEFENSIVE_END",
     "assignment": "Two-gap control; occupies the tackle."
    },
    {
     "id": "NT",
     "label": "NT",
     "x": 50,
     "y": 48,
     "role": "Nose Tackle",
     "position_ref": "POSITION_NOSE_TACKLE",
     "assignment": "Two-gaps the center; anchors the middle."
    },
    {
     "id": "DE2",
     "label": "DE",
     "x": 62,
     "y": 48,
     "role": "Defensive End",
     "position_ref": "POSITION_DEFENSIVE_END",
     "assignment": "Two-gap control; occupies the tackle."
    },
    {
     "id": "OLB1",
     "label": "OLB",
     "x": 22,
     "y": 42,
     "role": "Edge / Outside Linebacker",
     "position_ref": "POSITION_EDGE_OUTSIDE_LINEBACKER",
     "assignment": "Stands up off the line; edge rush or contain."
    },
    {
     "id": "ILB1",
     "label": "ILB",
     "x": 42,
     "y": 36,
     "role": "Mike Linebacker",
     "position_ref": "POSITION_MIKE_LINEBACKER",
     "assignment": "Interior run fit and coverage."
    },
    {
     "id": "ILB2",
     "label": "ILB",
     "x": 58,
     "y": 36,
     "role": "Will Linebacker",
     "position_ref": "POSITION_WILL_LINEBACKER",
     "assignment": "Interior run fit and coverage."
    },
    {
     "id": "OLB2",
     "label": "OLB",
     "x": 78,
     "y": 42,
     "role": "Edge / Outside Linebacker",
     "position_ref": "POSITION_EDGE_OUTSIDE_LINEBACKER",
     "assignment": "Stands up off the line; edge rush or contain."
    },
    {
     "id": "CB1",
     "label": "CB",
     "x": 8,
     "y": 42,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Outside coverage leverage."
    },
    {
     "id": "CB2",
     "label": "CB",
     "x": 92,
     "y": 42,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Outside coverage leverage."
    },
    {
     "id": "FS",
     "label": "FS",
     "x": 38,
     "y": 18,
     "role": "Free Safety",
     "position_ref": "POSITION_FREE_SAFETY",
     "assignment": "Deep help; last line vs. the pass."
    },
    {
     "id": "SS",
     "label": "SS",
     "x": 62,
     "y": 20,
     "role": "Strong Safety",
     "position_ref": "POSITION_STRONG_SAFETY",
     "assignment": "Run support and coverage vs. the tight end/slot."
    }
   ],
   "notes": "Three down linemen (usually two-gapping) and four linebackers, two of whom stand up as edge rushers -- can disguise which one comes on a given snap.",
   "description": "3-4: three down linemen, four linebackers (two standing as edge rushers), four defensive backs."
  },
  "DEFPERSONNEL_NICKEL_4_2_5": {
   "id": "DEFPERSONNEL_NICKEL_4_2_5",
   "side": "defense",
   "los_y": 50,
   "category": "front",
   "verified": true,
   "display_name": "Nickel (4-2-5)",
   "personnel": "4 DL / 2 LB / 5 DB",
   "players": [
    {
     "id": "LE",
     "label": "LE",
     "x": 37,
     "y": 48,
     "role": "Left Defensive End",
     "position_ref": "POSITION_DEFENSIVE_END",
     "assignment": "Sets the edge; contain rusher."
    },
    {
     "id": "DT1",
     "label": "DT",
     "x": 46,
     "y": 48,
     "role": "3-Technique",
     "position_ref": "POSITION_3_TECHNIQUE",
     "assignment": "Attacks the guard's outside shoulder."
    },
    {
     "id": "DT2",
     "label": "DT",
     "x": 54,
     "y": 48,
     "role": "Nose Tackle",
     "position_ref": "POSITION_NOSE_TACKLE",
     "assignment": "Occupies the interior."
    },
    {
     "id": "RE",
     "label": "RE",
     "x": 63,
     "y": 48,
     "role": "Right Defensive End",
     "position_ref": "POSITION_DEFENSIVE_END",
     "assignment": "Sets the edge; contain rusher."
    },
    {
     "id": "MLB",
     "label": "M",
     "x": 44,
     "y": 38,
     "role": "Mike Linebacker",
     "position_ref": "POSITION_MIKE_LINEBACKER",
     "assignment": "Downhill run fit; makes the call."
    },
    {
     "id": "WLB",
     "label": "W",
     "x": 56,
     "y": 38,
     "role": "Will Linebacker",
     "position_ref": "POSITION_WILL_LINEBACKER",
     "assignment": "Run fit and coverage -- replaces the base defense's third linebacker."
    },
    {
     "id": "CB1",
     "label": "CB",
     "x": 8,
     "y": 42,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Outside coverage leverage."
    },
    {
     "id": "CB2",
     "label": "CB",
     "x": 92,
     "y": 42,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Outside coverage leverage."
    },
    {
     "id": "NB",
     "label": "NB",
     "x": 25,
     "y": 38,
     "role": "Nickel / Star",
     "position_ref": "POSITION_NICKEL_STAR",
     "assignment": "The extra defensive back -- covers the slot receiver in place of a base linebacker."
    },
    {
     "id": "FS",
     "label": "FS",
     "x": 38,
     "y": 18,
     "role": "Free Safety",
     "position_ref": "POSITION_FREE_SAFETY",
     "assignment": "Deep help; last line vs. the pass."
    },
    {
     "id": "SS",
     "label": "SS",
     "x": 62,
     "y": 20,
     "role": "Strong Safety",
     "position_ref": "POSITION_STRONG_SAFETY",
     "assignment": "Run support and coverage."
    }
   ],
   "notes": "Base sub-package vs. 3-plus-receiver sets: a fifth defensive back (nickel/star) replaces the base defense's third linebacker to match receivers.",
   "description": "Nickel 4-2-5: four down linemen, two linebackers, five defensive backs including a nickel defender in the slot."
  },
  "DEFPERSONNEL_3_3_5_STACK": {
   "id": "DEFPERSONNEL_3_3_5_STACK",
   "side": "defense",
   "los_y": 50,
   "category": "front",
   "verified": true,
   "display_name": "3-3-5 Stack",
   "personnel": "3 DL / 3 LB / 5 DB",
   "players": [
    {
     "id": "DE1",
     "label": "DE",
     "x": 38,
     "y": 48,
     "role": "Defensive End",
     "position_ref": "POSITION_DEFENSIVE_END",
     "assignment": "Edge control."
    },
    {
     "id": "NT",
     "label": "NT",
     "x": 50,
     "y": 48,
     "role": "Nose Tackle",
     "position_ref": "POSITION_NOSE_TACKLE",
     "assignment": "Occupies the center."
    },
    {
     "id": "DE2",
     "label": "DE",
     "x": 62,
     "y": 48,
     "role": "Defensive End",
     "position_ref": "POSITION_DEFENSIVE_END",
     "assignment": "Edge control."
    },
    {
     "id": "LB1",
     "label": "LB",
     "x": 36,
     "y": 38,
     "role": "Linebacker",
     "position_ref": "POSITION_WILL_LINEBACKER",
     "assignment": "Stacked behind the line; run fit or blitz."
    },
    {
     "id": "LB2",
     "label": "LB",
     "x": 50,
     "y": 37,
     "role": "Mike Linebacker",
     "position_ref": "POSITION_MIKE_LINEBACKER",
     "assignment": "Stacked behind the nose; run fit or blitz."
    },
    {
     "id": "LB3",
     "label": "LB",
     "x": 64,
     "y": 38,
     "role": "Linebacker",
     "position_ref": "POSITION_SAM_LINEBACKER",
     "assignment": "Stacked behind the line; run fit or blitz."
    },
    {
     "id": "CB1",
     "label": "CB",
     "x": 8,
     "y": 42,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Outside coverage leverage."
    },
    {
     "id": "CB2",
     "label": "CB",
     "x": 92,
     "y": 42,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Outside coverage leverage."
    },
    {
     "id": "NB",
     "label": "NB",
     "x": 22,
     "y": 38,
     "role": "Nickel / Star",
     "position_ref": "POSITION_NICKEL_STAR",
     "assignment": "Covers the slot; extra run/blitz piece."
    },
    {
     "id": "FS",
     "label": "FS",
     "x": 38,
     "y": 18,
     "role": "Free Safety",
     "position_ref": "POSITION_FREE_SAFETY",
     "assignment": "Deep help."
    },
    {
     "id": "SS",
     "label": "SS",
     "x": 62,
     "y": 20,
     "role": "Strong Safety",
     "position_ref": "POSITION_STRONG_SAFETY",
     "assignment": "Run support and coverage."
    }
   ],
   "notes": "Three down linemen with three linebackers stacked directly behind them, disguising which (if any) of the three blitzes.",
   "description": "3-3-5 Stack: three down linemen, three stacked linebackers, five defensive backs."
  },
  "DEFPERSONNEL_DIME": {
   "id": "DEFPERSONNEL_DIME",
   "side": "defense",
   "los_y": 50,
   "category": "front",
   "verified": true,
   "display_name": "Dime",
   "personnel": "4 DL / 1 LB / 6 DB",
   "players": [
    {
     "id": "LE",
     "label": "LE",
     "x": 37,
     "y": 48,
     "role": "Left Defensive End",
     "position_ref": "POSITION_DEFENSIVE_END",
     "assignment": "Edge rush."
    },
    {
     "id": "DT1",
     "label": "DT",
     "x": 46,
     "y": 48,
     "role": "3-Technique",
     "position_ref": "POSITION_3_TECHNIQUE",
     "assignment": "Interior rush."
    },
    {
     "id": "DT2",
     "label": "DT",
     "x": 54,
     "y": 48,
     "role": "Nose Tackle",
     "position_ref": "POSITION_NOSE_TACKLE",
     "assignment": "Interior rush."
    },
    {
     "id": "RE",
     "label": "RE",
     "x": 63,
     "y": 48,
     "role": "Right Defensive End",
     "position_ref": "POSITION_DEFENSIVE_END",
     "assignment": "Edge rush."
    },
    {
     "id": "MLB",
     "label": "M",
     "x": 50,
     "y": 38,
     "role": "Mike Linebacker",
     "position_ref": "POSITION_MIKE_LINEBACKER",
     "assignment": "The lone linebacker; only run fitter underneath."
    },
    {
     "id": "CB1",
     "label": "CB",
     "x": 8,
     "y": 42,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Outside coverage leverage."
    },
    {
     "id": "CB2",
     "label": "CB",
     "x": 92,
     "y": 42,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Outside coverage leverage."
    },
    {
     "id": "NB1",
     "label": "NB",
     "x": 25,
     "y": 38,
     "role": "Nickel / Star",
     "position_ref": "POSITION_NICKEL_STAR",
     "assignment": "Covers a slot receiver."
    },
    {
     "id": "NB2",
     "label": "DB",
     "x": 75,
     "y": 38,
     "role": "Dime Back",
     "position_ref": "POSITION_NICKEL_STAR",
     "assignment": "Sixth defensive back -- covers the second slot receiver."
    },
    {
     "id": "FS",
     "label": "FS",
     "x": 38,
     "y": 18,
     "role": "Free Safety",
     "position_ref": "POSITION_FREE_SAFETY",
     "assignment": "Deep help."
    },
    {
     "id": "SS",
     "label": "SS",
     "x": 62,
     "y": 20,
     "role": "Strong Safety",
     "position_ref": "POSITION_STRONG_SAFETY",
     "assignment": "Deep help / coverage."
    }
   ],
   "notes": "Six defensive backs, down to a single linebacker -- an obvious passing-down package that sacrifices run support for coverage.",
   "description": "Dime: four down linemen, one linebacker, six defensive backs."
  },
  "FRONT_BEAR_FRONT": {
   "id": "FRONT_BEAR_FRONT",
   "side": "defense",
   "los_y": 50,
   "category": "front",
   "verified": true,
   "display_name": "Bear Front",
   "personnel": "5 DL / 2 LB / 4 DB",
   "players": [
    {
     "id": "E1",
     "label": "E",
     "x": 30,
     "y": 48,
     "role": "Defensive End",
     "position_ref": "POSITION_DEFENSIVE_END",
     "assignment": "5-technique on the tackle."
    },
    {
     "id": "T1",
     "label": "T",
     "x": 42,
     "y": 48,
     "role": "3-Technique",
     "position_ref": "POSITION_3_TECHNIQUE",
     "assignment": "Covers the guard."
    },
    {
     "id": "NT",
     "label": "NT",
     "x": 50,
     "y": 48,
     "role": "Nose Tackle",
     "position_ref": "POSITION_NOSE_TACKLE",
     "assignment": "Head-up on the center."
    },
    {
     "id": "T2",
     "label": "T",
     "x": 58,
     "y": 48,
     "role": "3-Technique",
     "position_ref": "POSITION_3_TECHNIQUE",
     "assignment": "Covers the guard."
    },
    {
     "id": "E2",
     "label": "E",
     "x": 70,
     "y": 48,
     "role": "Defensive End",
     "position_ref": "POSITION_DEFENSIVE_END",
     "assignment": "5-technique on the tackle."
    },
    {
     "id": "LB1",
     "label": "LB",
     "x": 44,
     "y": 36,
     "role": "Linebacker",
     "position_ref": "POSITION_MIKE_LINEBACKER",
     "assignment": "Flows behind a covered interior line."
    },
    {
     "id": "LB2",
     "label": "LB",
     "x": 56,
     "y": 36,
     "role": "Linebacker",
     "position_ref": "POSITION_WILL_LINEBACKER",
     "assignment": "Flows behind a covered interior line."
    },
    {
     "id": "CB1",
     "label": "CB",
     "x": 8,
     "y": 42,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Outside coverage leverage."
    },
    {
     "id": "CB2",
     "label": "CB",
     "x": 92,
     "y": 42,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Outside coverage leverage."
    },
    {
     "id": "FS",
     "label": "FS",
     "x": 38,
     "y": 18,
     "role": "Free Safety",
     "position_ref": "POSITION_FREE_SAFETY",
     "assignment": "Deep help."
    },
    {
     "id": "SS",
     "label": "SS",
     "x": 62,
     "y": 20,
     "role": "Strong Safety",
     "position_ref": "POSITION_STRONG_SAFETY",
     "assignment": "Run support."
    }
   ],
   "notes": "Five defensive linemen cover both guards, the center, and both tackles -- floods the interior to shut down inside runs, at the cost of light edge numbers.",
   "description": "Bear Front: five down linemen covering both guards, the center, and both tackles, with two linebackers behind."
  },
  "FRONT_4_3_OVER": {
   "id": "FRONT_4_3_OVER",
   "side": "defense",
   "los_y": 50,
   "category": "front",
   "verified": true,
   "display_name": "Over Front",
   "personnel": "4 DL / 3 LB / 4 DB",
   "players": [
    {
     "id": "LE",
     "label": "LE",
     "x": 34,
     "y": 48,
     "role": "Left Defensive End",
     "position_ref": "POSITION_DEFENSIVE_END",
     "assignment": "Weak-side 5-technique."
    },
    {
     "id": "T3",
     "label": "3T",
     "x": 48,
     "y": 48,
     "role": "3-Technique",
     "position_ref": "POSITION_3_TECHNIQUE",
     "assignment": "Shaded toward the strong side (toward the tight end)."
    },
    {
     "id": "T1",
     "label": "1T",
     "x": 56,
     "y": 48,
     "role": "Nose Tackle",
     "position_ref": "POSITION_NOSE_TACKLE",
     "assignment": "Shaded weak-side/away from the tight end."
    },
    {
     "id": "RE",
     "label": "RE",
     "x": 68,
     "y": 48,
     "role": "Right Defensive End",
     "position_ref": "POSITION_DEFENSIVE_END",
     "assignment": "Strong-side, often a wider 9-technique."
    },
    {
     "id": "SLB",
     "label": "S",
     "x": 74,
     "y": 36,
     "role": "Sam Linebacker",
     "position_ref": "POSITION_SAM_LINEBACKER",
     "assignment": "Walks up on the line, strong side, to balance the front."
    },
    {
     "id": "MLB",
     "label": "M",
     "x": 50,
     "y": 38,
     "role": "Mike Linebacker",
     "position_ref": "POSITION_MIKE_LINEBACKER",
     "assignment": "Downhill run fit."
    },
    {
     "id": "WLB",
     "label": "W",
     "x": 30,
     "y": 38,
     "role": "Will Linebacker",
     "position_ref": "POSITION_WILL_LINEBACKER",
     "assignment": "Weak-side run fit and coverage."
    },
    {
     "id": "CB1",
     "label": "CB",
     "x": 8,
     "y": 42,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Outside coverage leverage."
    },
    {
     "id": "CB2",
     "label": "CB",
     "x": 92,
     "y": 42,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Outside coverage leverage."
    },
    {
     "id": "FS",
     "label": "FS",
     "x": 38,
     "y": 18,
     "role": "Free Safety",
     "position_ref": "POSITION_FREE_SAFETY",
     "assignment": "Deep help."
    },
    {
     "id": "SS",
     "label": "SS",
     "x": 62,
     "y": 20,
     "role": "Strong Safety",
     "position_ref": "POSITION_STRONG_SAFETY",
     "assignment": "Run support vs. the tight end."
    }
   ],
   "notes": "\"Over\" describes which side the 3-technique defensive tackle lines up relative to the offense's declared strength (here, toward it) -- exact technique numbering varies by scheme, so treat this as illustrative, not universal.",
   "variation_note": "The strong-side/weak-side read depends on the offense's formation each snap -- this diagram fixes a strength side for illustration only.",
   "description": "Over Front: a 4-3 look with the 3-technique shifted toward the offense's formation strength."
  },
  "FRONT_4_3_UNDER": {
   "id": "FRONT_4_3_UNDER",
   "side": "defense",
   "los_y": 50,
   "category": "front",
   "verified": true,
   "display_name": "Under Front",
   "personnel": "4 DL / 3 LB / 4 DB",
   "players": [
    {
     "id": "LE",
     "label": "LE",
     "x": 32,
     "y": 48,
     "role": "Left Defensive End",
     "position_ref": "POSITION_DEFENSIVE_END",
     "assignment": "Strong-side, often a wider 9-technique."
    },
    {
     "id": "T1",
     "label": "1T",
     "x": 44,
     "y": 48,
     "role": "Nose Tackle",
     "position_ref": "POSITION_NOSE_TACKLE",
     "assignment": "Shaded toward the strong side."
    },
    {
     "id": "T3",
     "label": "3T",
     "x": 52,
     "y": 48,
     "role": "3-Technique",
     "position_ref": "POSITION_3_TECHNIQUE",
     "assignment": "Shaded weak-side/away from the tight end."
    },
    {
     "id": "RE",
     "label": "RE",
     "x": 66,
     "y": 48,
     "role": "Right Defensive End",
     "position_ref": "POSITION_DEFENSIVE_END",
     "assignment": "Weak-side 5-technique."
    },
    {
     "id": "SLB",
     "label": "S",
     "x": 26,
     "y": 36,
     "role": "Sam Linebacker",
     "position_ref": "POSITION_SAM_LINEBACKER",
     "assignment": "Sits off the line, strong side."
    },
    {
     "id": "MLB",
     "label": "M",
     "x": 50,
     "y": 38,
     "role": "Mike Linebacker",
     "position_ref": "POSITION_MIKE_LINEBACKER",
     "assignment": "Downhill run fit."
    },
    {
     "id": "WLB",
     "label": "W",
     "x": 70,
     "y": 38,
     "role": "Will Linebacker",
     "position_ref": "POSITION_WILL_LINEBACKER",
     "assignment": "Weak-side run fit and coverage."
    },
    {
     "id": "CB1",
     "label": "CB",
     "x": 8,
     "y": 42,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Outside coverage leverage."
    },
    {
     "id": "CB2",
     "label": "CB",
     "x": 92,
     "y": 42,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Outside coverage leverage."
    },
    {
     "id": "FS",
     "label": "FS",
     "x": 38,
     "y": 18,
     "role": "Free Safety",
     "position_ref": "POSITION_FREE_SAFETY",
     "assignment": "Deep help."
    },
    {
     "id": "SS",
     "label": "SS",
     "x": 62,
     "y": 20,
     "role": "Strong Safety",
     "position_ref": "POSITION_STRONG_SAFETY",
     "assignment": "Run support vs. the tight end."
    }
   ],
   "notes": "\"Under\" shifts the 3-technique to the weak side (away from the offense's strength) -- the mirror image of the Over front. The Sam linebacker often walks up to the line strong-side to compensate for the lighter strong-side surface.",
   "variation_note": "The strong-side/weak-side read depends on the offense's formation each snap -- this diagram fixes a strength side for illustration only.",
   "description": "Under Front: a 4-3 look with the 3-technique shifted away from the offense's formation strength."
  },
  "FRONT_ODD_FRONT": {
   "id": "FRONT_ODD_FRONT",
   "side": "defense",
   "los_y": 50,
   "category": "front",
   "verified": true,
   "display_name": "Odd Front",
   "personnel": "3 DL / 4 LB / 4 DB",
   "players": [
    {
     "id": "DE1",
     "label": "DE",
     "x": 40,
     "y": 48,
     "role": "Defensive End",
     "position_ref": "POSITION_DEFENSIVE_END",
     "assignment": "Aligns over the guard-tackle gap."
    },
    {
     "id": "NT",
     "label": "NT",
     "x": 50,
     "y": 48,
     "role": "Nose Tackle",
     "position_ref": "POSITION_NOSE_TACKLE",
     "assignment": "Head-up on the center."
    },
    {
     "id": "DE2",
     "label": "DE",
     "x": 60,
     "y": 48,
     "role": "Defensive End",
     "position_ref": "POSITION_DEFENSIVE_END",
     "assignment": "Aligns over the guard-tackle gap."
    },
    {
     "id": "LB1",
     "label": "LB",
     "x": 34,
     "y": 36,
     "role": "Linebacker",
     "position_ref": "POSITION_WILL_LINEBACKER",
     "assignment": "Stacked behind an odd-front gap."
    },
    {
     "id": "LB2",
     "label": "LB",
     "x": 46,
     "y": 36,
     "role": "Mike Linebacker",
     "position_ref": "POSITION_MIKE_LINEBACKER",
     "assignment": "Stacked behind the nose."
    },
    {
     "id": "LB3",
     "label": "LB",
     "x": 54,
     "y": 36,
     "role": "Linebacker",
     "position_ref": "POSITION_SAM_LINEBACKER",
     "assignment": "Stacked behind the nose."
    },
    {
     "id": "LB4",
     "label": "LB",
     "x": 66,
     "y": 36,
     "role": "Linebacker",
     "position_ref": "POSITION_EDGE_OUTSIDE_LINEBACKER",
     "assignment": "Stacked behind an odd-front gap."
    },
    {
     "id": "CB1",
     "label": "CB",
     "x": 8,
     "y": 42,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Outside coverage leverage."
    },
    {
     "id": "CB2",
     "label": "CB",
     "x": 92,
     "y": 42,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Outside coverage leverage."
    },
    {
     "id": "FS",
     "label": "FS",
     "x": 38,
     "y": 18,
     "role": "Free Safety",
     "position_ref": "POSITION_FREE_SAFETY",
     "assignment": "Deep help."
    },
    {
     "id": "SS",
     "label": "SS",
     "x": 62,
     "y": 20,
     "role": "Strong Safety",
     "position_ref": "POSITION_STRONG_SAFETY",
     "assignment": "Run support."
    }
   ],
   "notes": "\"Odd\" describes an odd number of linemen on the line of scrimmage (three, nose over the center) -- the 3-4's front family in general, regardless of the specific linebacker package behind it.",
   "description": "Odd Front: three down linemen with the nose head-up on the center, four linebackers stacked behind the line's gaps."
  },
  "FRONT_EVEN": {
   "id": "FRONT_EVEN",
   "side": "defense",
   "los_y": 50,
   "category": "front",
   "verified": true,
   "display_name": "Even Front",
   "personnel": "4 DL / 3 LB / 4 DB",
   "players": [
    {
     "id": "LE",
     "label": "LE",
     "x": 36,
     "y": 48,
     "role": "Left Defensive End",
     "position_ref": "POSITION_DEFENSIVE_END",
     "assignment": "Symmetric 5-technique."
    },
    {
     "id": "T1",
     "label": "T",
     "x": 45,
     "y": 48,
     "role": "3-Technique",
     "position_ref": "POSITION_3_TECHNIQUE",
     "assignment": "Symmetric interior alignment."
    },
    {
     "id": "T2",
     "label": "T",
     "x": 55,
     "y": 48,
     "role": "3-Technique",
     "position_ref": "POSITION_3_TECHNIQUE",
     "assignment": "Symmetric interior alignment."
    },
    {
     "id": "RE",
     "label": "RE",
     "x": 64,
     "y": 48,
     "role": "Right Defensive End",
     "position_ref": "POSITION_DEFENSIVE_END",
     "assignment": "Symmetric 5-technique."
    },
    {
     "id": "WLB",
     "label": "W",
     "x": 30,
     "y": 38,
     "role": "Will Linebacker",
     "position_ref": "POSITION_WILL_LINEBACKER",
     "assignment": "Run fit and coverage."
    },
    {
     "id": "MLB",
     "label": "M",
     "x": 50,
     "y": 36,
     "role": "Mike Linebacker",
     "position_ref": "POSITION_MIKE_LINEBACKER",
     "assignment": "Downhill run fit."
    },
    {
     "id": "SLB",
     "label": "S",
     "x": 70,
     "y": 38,
     "role": "Sam Linebacker",
     "position_ref": "POSITION_SAM_LINEBACKER",
     "assignment": "Run fit vs. the tight end."
    },
    {
     "id": "CB1",
     "label": "CB",
     "x": 8,
     "y": 42,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Outside coverage leverage."
    },
    {
     "id": "CB2",
     "label": "CB",
     "x": 92,
     "y": 42,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Outside coverage leverage."
    },
    {
     "id": "FS",
     "label": "FS",
     "x": 38,
     "y": 18,
     "role": "Free Safety",
     "position_ref": "POSITION_FREE_SAFETY",
     "assignment": "Deep help."
    },
    {
     "id": "SS",
     "label": "SS",
     "x": 62,
     "y": 20,
     "role": "Strong Safety",
     "position_ref": "POSITION_STRONG_SAFETY",
     "assignment": "Run support."
    }
   ],
   "notes": "\"Even\" describes an even number of linemen on the line (four), aligned symmetrically rather than shaded Over or Under toward a strength side.",
   "description": "Even Front: four down linemen aligned symmetrically, three linebackers behind."
  }
 },
 "coverages": {
  "COVER_0": {
   "id": "COVER_0",
   "side": "defense",
   "los_y": 50,
   "category": "coverage",
   "verified": true,
   "display_name": "Cover 0",
   "shell": "No deep safety",
   "players": [
    {
     "id": "oWR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "ghost": true,
     "role": "Wide Receiver"
    },
    {
     "id": "oWR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "ghost": true,
     "role": "Wide Receiver"
    },
    {
     "id": "oSL",
     "label": "SL",
     "x": 80,
     "y": 48,
     "ghost": true,
     "role": "Slot Receiver"
    },
    {
     "id": "oTE",
     "label": "TE",
     "x": 24,
     "y": 50,
     "ghost": true,
     "role": "Tight End"
    },
    {
     "id": "oRB",
     "label": "RB",
     "x": 50,
     "y": 58,
     "ghost": true,
     "role": "Running Back"
    },
    {
     "id": "CB1",
     "label": "CB",
     "x": 6,
     "y": 46,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Press man on the outside WR -- no deep help."
    },
    {
     "id": "CB2",
     "label": "CB",
     "x": 94,
     "y": 46,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Press man on the outside WR -- no deep help."
    },
    {
     "id": "NB",
     "label": "NB",
     "x": 80,
     "y": 42,
     "role": "Nickel / Star",
     "position_ref": "POSITION_NICKEL_STAR",
     "assignment": "Man on the slot receiver."
    },
    {
     "id": "SS",
     "label": "SS",
     "x": 24,
     "y": 40,
     "role": "Strong Safety",
     "position_ref": "POSITION_STRONG_SAFETY",
     "assignment": "Man on the tight end -- no deep-half responsibility."
    },
    {
     "id": "FS",
     "label": "FS",
     "x": 50,
     "y": 32,
     "role": "Free Safety",
     "position_ref": "POSITION_FREE_SAFETY",
     "assignment": "Man/spy on the running back, or an extra rusher -- no deep zone."
    },
    {
     "id": "LB",
     "label": "LB",
     "x": 46,
     "y": 40,
     "role": "Mike Linebacker",
     "position_ref": "POSITION_MIKE_LINEBACKER",
     "assignment": "Blitzes or spies -- every eligible receiver is covered man-to-man."
    }
   ],
   "man_coverage": true,
   "zones": [],
   "weaknesses": "No deep safety help -- a single blown man matchup or a receiver winning his release becomes an explosive play with nobody to bail it out.",
   "description": "Cover 0: every eligible receiver covered man-to-man with no deep safety help -- an all-out pressure look."
  },
  "COVER_1": {
   "id": "COVER_1",
   "side": "defense",
   "los_y": 50,
   "category": "coverage",
   "verified": true,
   "display_name": "Cover 1 (Man-Free)",
   "shell": "Single-high safety",
   "players": [
    {
     "id": "oWR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "ghost": true,
     "role": "Wide Receiver"
    },
    {
     "id": "oWR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "ghost": true,
     "role": "Wide Receiver"
    },
    {
     "id": "oSL",
     "label": "SL",
     "x": 80,
     "y": 48,
     "ghost": true,
     "role": "Slot Receiver"
    },
    {
     "id": "oTE",
     "label": "TE",
     "x": 24,
     "y": 50,
     "ghost": true,
     "role": "Tight End"
    },
    {
     "id": "oRB",
     "label": "RB",
     "x": 50,
     "y": 58,
     "ghost": true,
     "role": "Running Back"
    },
    {
     "id": "CB1",
     "label": "CB",
     "x": 6,
     "y": 46,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Man on the outside WR."
    },
    {
     "id": "CB2",
     "label": "CB",
     "x": 94,
     "y": 46,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Man on the outside WR."
    },
    {
     "id": "NB",
     "label": "NB",
     "x": 80,
     "y": 42,
     "role": "Nickel / Star",
     "position_ref": "POSITION_NICKEL_STAR",
     "assignment": "Man on the slot receiver."
    },
    {
     "id": "SS",
     "label": "SS",
     "x": 24,
     "y": 38,
     "role": "Strong Safety",
     "position_ref": "POSITION_STRONG_SAFETY",
     "assignment": "Man on the tight end, or a robber/spy underneath."
    },
    {
     "id": "LB",
     "label": "LB",
     "x": 50,
     "y": 40,
     "role": "Mike Linebacker",
     "position_ref": "POSITION_MIKE_LINEBACKER",
     "assignment": "Man on the running back out of the backfield."
    },
    {
     "id": "FS",
     "label": "FS",
     "x": 50,
     "y": 14,
     "role": "Free Safety",
     "position_ref": "POSITION_FREE_SAFETY",
     "assignment": "The lone deep defender -- the \"free\" safety, unblocked and reading the quarterback."
    }
   ],
   "man_coverage": true,
   "zones": [
    {
     "label": "Deep Middle (Free Safety)",
     "cx": 50,
     "cy": 12,
     "rx": 26,
     "ry": 10
    }
   ],
   "weaknesses": "One deep defender covers the entire field -- a receiver who wins deep leverage against his man can outrun the single safety over the top.",
   "description": "Cover 1: man coverage on every eligible receiver with one free safety deep in the middle of the field."
  },
  "COVER_2": {
   "id": "COVER_2",
   "side": "defense",
   "los_y": 50,
   "category": "coverage",
   "verified": true,
   "display_name": "Cover 2",
   "shell": "Two-high safety",
   "players": [
    {
     "id": "oWR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "ghost": true,
     "role": "Wide Receiver"
    },
    {
     "id": "oWR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "ghost": true,
     "role": "Wide Receiver"
    },
    {
     "id": "oSL",
     "label": "SL",
     "x": 80,
     "y": 48,
     "ghost": true,
     "role": "Slot Receiver"
    },
    {
     "id": "oTE",
     "label": "TE",
     "x": 24,
     "y": 50,
     "ghost": true,
     "role": "Tight End"
    },
    {
     "id": "oRB",
     "label": "RB",
     "x": 50,
     "y": 58,
     "ghost": true,
     "role": "Running Back"
    },
    {
     "id": "CB1",
     "label": "CB",
     "x": 8,
     "y": 44,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Jams the WR, then sinks to the flat -- underneath zone, not deep."
    },
    {
     "id": "CB2",
     "label": "CB",
     "x": 92,
     "y": 44,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Jams the WR, then sinks to the flat -- underneath zone, not deep."
    },
    {
     "id": "NB",
     "label": "NB",
     "x": 80,
     "y": 40,
     "role": "Nickel / Star",
     "position_ref": "POSITION_NICKEL_STAR",
     "assignment": "Underneath flat/curl zone."
    },
    {
     "id": "LB1",
     "label": "LB",
     "x": 34,
     "y": 36,
     "role": "Will Linebacker",
     "position_ref": "POSITION_WILL_LINEBACKER",
     "assignment": "Underneath hook/curl zone."
    },
    {
     "id": "LB2",
     "label": "LB",
     "x": 50,
     "y": 36,
     "role": "Mike Linebacker",
     "position_ref": "POSITION_MIKE_LINEBACKER",
     "assignment": "Underneath middle hook zone."
    },
    {
     "id": "LB3",
     "label": "LB",
     "x": 66,
     "y": 36,
     "role": "Sam Linebacker",
     "position_ref": "POSITION_SAM_LINEBACKER",
     "assignment": "Underneath hook/curl zone."
    },
    {
     "id": "FS",
     "label": "FS",
     "x": 32,
     "y": 16,
     "role": "Free Safety",
     "position_ref": "POSITION_FREE_SAFETY",
     "assignment": "Deep half zone (left)."
    },
    {
     "id": "SS",
     "label": "SS",
     "x": 68,
     "y": 16,
     "role": "Strong Safety",
     "position_ref": "POSITION_STRONG_SAFETY",
     "assignment": "Deep half zone (right)."
    }
   ],
   "zones": [
    {
     "label": "Deep Half (L)",
     "cx": 30,
     "cy": 12,
     "rx": 24,
     "ry": 9
    },
    {
     "label": "Deep Half (R)",
     "cx": 70,
     "cy": 12,
     "rx": 24,
     "ry": 9
    }
   ],
   "weaknesses": "The deep middle seam, between the two safeties, and the deep sideline behind the corners (who are underneath, not deep) are the classic Cover 2 soft spots.",
   "description": "Cover 2: two deep-half safeties, five underneath zone defenders, corners playing the flat rather than deep."
  },
  "TAMPA_2": {
   "id": "TAMPA_2",
   "side": "defense",
   "los_y": 50,
   "category": "coverage",
   "verified": true,
   "display_name": "Tampa 2",
   "shell": "Two-high safety",
   "players": [
    {
     "id": "oWR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "ghost": true,
     "role": "Wide Receiver"
    },
    {
     "id": "oWR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "ghost": true,
     "role": "Wide Receiver"
    },
    {
     "id": "oSL",
     "label": "SL",
     "x": 80,
     "y": 48,
     "ghost": true,
     "role": "Slot Receiver"
    },
    {
     "id": "oTE",
     "label": "TE",
     "x": 24,
     "y": 50,
     "ghost": true,
     "role": "Tight End"
    },
    {
     "id": "oRB",
     "label": "RB",
     "x": 50,
     "y": 58,
     "ghost": true,
     "role": "Running Back"
    },
    {
     "id": "CB1",
     "label": "CB",
     "x": 8,
     "y": 44,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Jams the WR, then sinks to the flat."
    },
    {
     "id": "CB2",
     "label": "CB",
     "x": 92,
     "y": 44,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Jams the WR, then sinks to the flat."
    },
    {
     "id": "NB",
     "label": "NB",
     "x": 80,
     "y": 40,
     "role": "Nickel / Star",
     "position_ref": "POSITION_NICKEL_STAR",
     "assignment": "Underneath flat/curl zone."
    },
    {
     "id": "LB1",
     "label": "LB",
     "x": 34,
     "y": 36,
     "role": "Will Linebacker",
     "position_ref": "POSITION_WILL_LINEBACKER",
     "assignment": "Underneath hook/curl zone."
    },
    {
     "id": "LB2",
     "label": "LB",
     "x": 50,
     "y": 26,
     "role": "Mike Linebacker",
     "position_ref": "POSITION_MIKE_LINEBACKER",
     "assignment": "Drops deep down the middle seam -- the defining Tampa 2 wrinkle that a standard Cover 2 doesn't have."
    },
    {
     "id": "LB3",
     "label": "LB",
     "x": 66,
     "y": 36,
     "role": "Sam Linebacker",
     "position_ref": "POSITION_SAM_LINEBACKER",
     "assignment": "Underneath hook/curl zone."
    },
    {
     "id": "FS",
     "label": "FS",
     "x": 32,
     "y": 14,
     "role": "Free Safety",
     "position_ref": "POSITION_FREE_SAFETY",
     "assignment": "Deep half zone (left)."
    },
    {
     "id": "SS",
     "label": "SS",
     "x": 68,
     "y": 14,
     "role": "Strong Safety",
     "position_ref": "POSITION_STRONG_SAFETY",
     "assignment": "Deep half zone (right)."
    }
   ],
   "zones": [
    {
     "label": "Deep Half (L)",
     "cx": 30,
     "cy": 11,
     "rx": 24,
     "ry": 8
    },
    {
     "label": "Deep Half (R)",
     "cx": 70,
     "cy": 11,
     "rx": 24,
     "ry": 8
    },
    {
     "label": "Mike's Deep Middle Drop",
     "cx": 50,
     "cy": 22,
     "rx": 12,
     "ry": 9
    }
   ],
   "weaknesses": "Closes Cover 2's deep-middle seam, but now leans on the Mike linebacker's athleticism and depth -- a fast enough seam route can still outrun him before he gets there.",
   "description": "Tampa 2: standard Cover 2 shell with the Mike linebacker dropping deep down the middle to close the seam between the safeties."
  },
  "COVER_3": {
   "id": "COVER_3",
   "side": "defense",
   "los_y": 50,
   "category": "coverage",
   "verified": true,
   "display_name": "Cover 3",
   "shell": "Single-high safety",
   "players": [
    {
     "id": "oWR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "ghost": true,
     "role": "Wide Receiver"
    },
    {
     "id": "oWR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "ghost": true,
     "role": "Wide Receiver"
    },
    {
     "id": "oSL",
     "label": "SL",
     "x": 80,
     "y": 48,
     "ghost": true,
     "role": "Slot Receiver"
    },
    {
     "id": "oTE",
     "label": "TE",
     "x": 24,
     "y": 50,
     "ghost": true,
     "role": "Tight End"
    },
    {
     "id": "oRB",
     "label": "RB",
     "x": 50,
     "y": 58,
     "ghost": true,
     "role": "Running Back"
    },
    {
     "id": "CB1",
     "label": "CB",
     "x": 8,
     "y": 30,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Deep outside third."
    },
    {
     "id": "CB2",
     "label": "CB",
     "x": 92,
     "y": 30,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Deep outside third."
    },
    {
     "id": "NB",
     "label": "NB",
     "x": 80,
     "y": 40,
     "role": "Nickel / Star",
     "position_ref": "POSITION_NICKEL_STAR",
     "assignment": "Underneath flat/curl zone."
    },
    {
     "id": "LB1",
     "label": "LB",
     "x": 34,
     "y": 36,
     "role": "Will Linebacker",
     "position_ref": "POSITION_WILL_LINEBACKER",
     "assignment": "Underneath hook/curl zone."
    },
    {
     "id": "LB2",
     "label": "LB",
     "x": 50,
     "y": 36,
     "role": "Mike Linebacker",
     "position_ref": "POSITION_MIKE_LINEBACKER",
     "assignment": "Underneath middle hook zone."
    },
    {
     "id": "LB3",
     "label": "LB",
     "x": 66,
     "y": 36,
     "role": "Sam Linebacker",
     "position_ref": "POSITION_SAM_LINEBACKER",
     "assignment": "Underneath hook/curl zone."
    },
    {
     "id": "FS",
     "label": "FS",
     "x": 50,
     "y": 14,
     "role": "Free Safety",
     "position_ref": "POSITION_FREE_SAFETY",
     "assignment": "Deep middle third."
    }
   ],
   "zones": [
    {
     "label": "Deep Third (L)",
     "cx": 17,
     "cy": 12,
     "rx": 17,
     "ry": 9
    },
    {
     "label": "Deep Third (Middle)",
     "cx": 50,
     "cy": 12,
     "rx": 17,
     "ry": 9
    },
    {
     "label": "Deep Third (R)",
     "cx": 83,
     "cy": 12,
     "rx": 17,
     "ry": 9
    }
   ],
   "weaknesses": "The deep out route, thrown into the void between a cornerback's deep-third zone and the underneath flat defender, is Cover 3's best-known vulnerability.",
   "description": "Cover 3: three deep-third defenders (both corners and the free safety), four underneath zones, single-high safety look pre-snap."
  },
  "COVER_4": {
   "id": "COVER_4",
   "side": "defense",
   "los_y": 50,
   "category": "coverage",
   "verified": true,
   "display_name": "Cover 4 (Quarters)",
   "shell": "Two-high safety",
   "players": [
    {
     "id": "oWR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "ghost": true,
     "role": "Wide Receiver"
    },
    {
     "id": "oWR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "ghost": true,
     "role": "Wide Receiver"
    },
    {
     "id": "oSL",
     "label": "SL",
     "x": 80,
     "y": 48,
     "ghost": true,
     "role": "Slot Receiver"
    },
    {
     "id": "oTE",
     "label": "TE",
     "x": 24,
     "y": 50,
     "ghost": true,
     "role": "Tight End"
    },
    {
     "id": "oRB",
     "label": "RB",
     "x": 50,
     "y": 58,
     "ghost": true,
     "role": "Running Back"
    },
    {
     "id": "CB1",
     "label": "CB",
     "x": 8,
     "y": 26,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Deep outside quarter."
    },
    {
     "id": "CB2",
     "label": "CB",
     "x": 92,
     "y": 26,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Deep outside quarter."
    },
    {
     "id": "NB",
     "label": "NB",
     "x": 80,
     "y": 40,
     "role": "Nickel / Star",
     "position_ref": "POSITION_NICKEL_STAR",
     "assignment": "Underneath flat/curl zone, matches the slot vertically if he releases deep."
    },
    {
     "id": "LB1",
     "label": "LB",
     "x": 34,
     "y": 36,
     "role": "Will Linebacker",
     "position_ref": "POSITION_WILL_LINEBACKER",
     "assignment": "Underneath hook/curl zone."
    },
    {
     "id": "LB2",
     "label": "LB",
     "x": 50,
     "y": 36,
     "role": "Mike Linebacker",
     "position_ref": "POSITION_MIKE_LINEBACKER",
     "assignment": "Underneath middle hook zone."
    },
    {
     "id": "FS",
     "label": "FS",
     "x": 30,
     "y": 14,
     "role": "Free Safety",
     "position_ref": "POSITION_FREE_SAFETY",
     "assignment": "Deep inside quarter."
    },
    {
     "id": "SS",
     "label": "SS",
     "x": 70,
     "y": 14,
     "role": "Strong Safety",
     "position_ref": "POSITION_STRONG_SAFETY",
     "assignment": "Deep inside quarter."
    }
   ],
   "zones": [
    {
     "label": "Deep Quarter (1)",
     "cx": 12,
     "cy": 11,
     "rx": 14,
     "ry": 8
    },
    {
     "label": "Deep Quarter (2)",
     "cx": 37,
     "cy": 11,
     "rx": 14,
     "ry": 8
    },
    {
     "label": "Deep Quarter (3)",
     "cx": 63,
     "cy": 11,
     "rx": 14,
     "ry": 8
    },
    {
     "label": "Deep Quarter (4)",
     "cx": 88,
     "cy": 11,
     "rx": 14,
     "ry": 8
    }
   ],
   "weaknesses": "Four deep defenders means strong vertical coverage, but the safeties' run-support/coverage rules can be manipulated by play action and switch releases that stress who has which quarter.",
   "description": "Cover 4 (Quarters): four deep-quarter defenders (both corners and both safeties), two-high shell pre-snap."
  },
  "COVER_6": {
   "id": "COVER_6",
   "side": "defense",
   "los_y": 50,
   "category": "coverage",
   "verified": true,
   "display_name": "Cover 6 (Quarter-Quarter-Half)",
   "shell": "Two-high safety (asymmetric)",
   "players": [
    {
     "id": "oWR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "ghost": true,
     "role": "Wide Receiver"
    },
    {
     "id": "oWR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "ghost": true,
     "role": "Wide Receiver"
    },
    {
     "id": "oSL",
     "label": "SL",
     "x": 80,
     "y": 48,
     "ghost": true,
     "role": "Slot Receiver"
    },
    {
     "id": "oTE",
     "label": "TE",
     "x": 24,
     "y": 50,
     "ghost": true,
     "role": "Tight End"
    },
    {
     "id": "oRB",
     "label": "RB",
     "x": 50,
     "y": 58,
     "ghost": true,
     "role": "Running Back"
    },
    {
     "id": "CB1",
     "label": "CB",
     "x": 8,
     "y": 44,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Deep half (boundary/short side)."
    },
    {
     "id": "CB2",
     "label": "CB",
     "x": 92,
     "y": 26,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Deep quarter (field/wide side)."
    },
    {
     "id": "NB",
     "label": "NB",
     "x": 80,
     "y": 40,
     "role": "Nickel / Star",
     "position_ref": "POSITION_NICKEL_STAR",
     "assignment": "Underneath flat/curl zone, field side."
    },
    {
     "id": "LB1",
     "label": "LB",
     "x": 34,
     "y": 36,
     "role": "Will Linebacker",
     "position_ref": "POSITION_WILL_LINEBACKER",
     "assignment": "Underneath hook/curl zone."
    },
    {
     "id": "LB2",
     "label": "LB",
     "x": 50,
     "y": 36,
     "role": "Mike Linebacker",
     "position_ref": "POSITION_MIKE_LINEBACKER",
     "assignment": "Underneath middle hook zone."
    },
    {
     "id": "FS",
     "label": "FS",
     "x": 24,
     "y": 16,
     "role": "Free Safety",
     "position_ref": "POSITION_FREE_SAFETY",
     "assignment": "Deep half (boundary side, splits it with the corner)."
    },
    {
     "id": "SS",
     "label": "SS",
     "x": 70,
     "y": 14,
     "role": "Strong Safety",
     "position_ref": "POSITION_STRONG_SAFETY",
     "assignment": "Deep quarter (field side)."
    }
   ],
   "zones": [
    {
     "label": "Deep Half (Boundary)",
     "cx": 20,
     "cy": 12,
     "rx": 22,
     "ry": 9
    },
    {
     "label": "Deep Quarter (Field)",
     "cx": 63,
     "cy": 11,
     "rx": 14,
     "ry": 8
    },
    {
     "label": "Deep Quarter (Field)",
     "cx": 88,
     "cy": 11,
     "rx": 14,
     "ry": 8
    }
   ],
   "weaknesses": "Splits the field: Cover 2 rules to the boundary (short side), Cover 4 rules to the field (wide side) -- exploited by attacking whichever half is actually weaker for a given hash/formation.",
   "description": "Cover 6: Cover 2 rules to one half of the field and Cover 4 rules to the other, splitting the field asymmetrically."
  },
  "MAN_COVERAGE": {
   "id": "MAN_COVERAGE",
   "side": "defense",
   "los_y": 50,
   "category": "coverage",
   "verified": true,
   "display_name": "Man Coverage",
   "shell": "Varies (0/1 shell shown)",
   "players": [
    {
     "id": "oWR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "ghost": true,
     "role": "Wide Receiver"
    },
    {
     "id": "oWR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "ghost": true,
     "role": "Wide Receiver"
    },
    {
     "id": "oSL",
     "label": "SL",
     "x": 80,
     "y": 48,
     "ghost": true,
     "role": "Slot Receiver"
    },
    {
     "id": "oTE",
     "label": "TE",
     "x": 24,
     "y": 50,
     "ghost": true,
     "role": "Tight End"
    },
    {
     "id": "oRB",
     "label": "RB",
     "x": 50,
     "y": 58,
     "ghost": true,
     "role": "Running Back"
    },
    {
     "id": "CB1",
     "label": "CB",
     "x": 6,
     "y": 46,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Assigned to one specific receiver for the entire play, regardless of where he runs."
    },
    {
     "id": "CB2",
     "label": "CB",
     "x": 94,
     "y": 46,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Assigned to one specific receiver for the entire play."
    },
    {
     "id": "NB",
     "label": "NB",
     "x": 80,
     "y": 42,
     "role": "Nickel / Star",
     "position_ref": "POSITION_NICKEL_STAR",
     "assignment": "Man on the slot receiver."
    },
    {
     "id": "SS",
     "label": "SS",
     "x": 24,
     "y": 40,
     "role": "Strong Safety",
     "position_ref": "POSITION_STRONG_SAFETY",
     "assignment": "Man on the tight end."
    },
    {
     "id": "FS",
     "label": "FS",
     "x": 50,
     "y": 14,
     "role": "Free Safety",
     "position_ref": "POSITION_FREE_SAFETY",
     "assignment": "Deep help over the top, if the shell has one (Cover 1) -- or another man assignment if it doesn't (Cover 0)."
    },
    {
     "id": "LB",
     "label": "LB",
     "x": 50,
     "y": 38,
     "role": "Mike Linebacker",
     "position_ref": "POSITION_MIKE_LINEBACKER",
     "assignment": "Man on the running back out of the backfield."
    }
   ],
   "man_coverage": true,
   "zones": [],
   "weaknesses": "Man coverage lives and dies on individual matchups -- a receiver who wins his release or a coverage defender who loses leverage gives up the play regardless of scheme.",
   "description": "Man Coverage: each defender assigned to one specific offensive player for the entire play, tracking him wherever he goes."
  },
  "ZONE_COVERAGE": {
   "id": "ZONE_COVERAGE",
   "side": "defense",
   "los_y": 50,
   "category": "coverage",
   "verified": true,
   "display_name": "Zone Coverage",
   "shell": "Varies (Cover 3 shell shown)",
   "players": [
    {
     "id": "oWR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "ghost": true,
     "role": "Wide Receiver"
    },
    {
     "id": "oWR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "ghost": true,
     "role": "Wide Receiver"
    },
    {
     "id": "oSL",
     "label": "SL",
     "x": 80,
     "y": 48,
     "ghost": true,
     "role": "Slot Receiver"
    },
    {
     "id": "oTE",
     "label": "TE",
     "x": 24,
     "y": 50,
     "ghost": true,
     "role": "Tight End"
    },
    {
     "id": "oRB",
     "label": "RB",
     "x": 50,
     "y": 58,
     "ghost": true,
     "role": "Running Back"
    },
    {
     "id": "CB1",
     "label": "CB",
     "x": 8,
     "y": 30,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Owns an area of the field, not a specific receiver -- passes receivers off as they enter/leave the zone."
    },
    {
     "id": "CB2",
     "label": "CB",
     "x": 92,
     "y": 30,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Owns an area of the field."
    },
    {
     "id": "LB1",
     "label": "LB",
     "x": 34,
     "y": 36,
     "role": "Will Linebacker",
     "position_ref": "POSITION_WILL_LINEBACKER",
     "assignment": "Underneath zone."
    },
    {
     "id": "LB2",
     "label": "LB",
     "x": 50,
     "y": 36,
     "role": "Mike Linebacker",
     "position_ref": "POSITION_MIKE_LINEBACKER",
     "assignment": "Underneath zone."
    },
    {
     "id": "LB3",
     "label": "LB",
     "x": 66,
     "y": 36,
     "role": "Sam Linebacker",
     "position_ref": "POSITION_SAM_LINEBACKER",
     "assignment": "Underneath zone."
    },
    {
     "id": "FS",
     "label": "FS",
     "x": 50,
     "y": 14,
     "role": "Free Safety",
     "position_ref": "POSITION_FREE_SAFETY",
     "assignment": "Deep zone."
    }
   ],
   "zones": [
    {
     "label": "Deep Third (L)",
     "cx": 17,
     "cy": 12,
     "rx": 17,
     "ry": 9
    },
    {
     "label": "Deep Third (Middle)",
     "cx": 50,
     "cy": 12,
     "rx": 17,
     "ry": 9
    },
    {
     "label": "Deep Third (R)",
     "cx": 83,
     "cy": 12,
     "rx": 17,
     "ry": 9
    }
   ],
   "weaknesses": "Zone defenders read the quarterback and route combinations rather than one man -- vulnerable to route distributions that overload one zone or exploit the seams between adjacent defenders.",
   "description": "Zone Coverage: each defender owns an area of the field rather than a specific receiver, passing receivers off between zones."
  },
  "MATCH_COVERAGE": {
   "id": "MATCH_COVERAGE",
   "side": "defense",
   "los_y": 50,
   "category": "coverage",
   "verified": true,
   "display_name": "Match Coverage",
   "shell": "Two-high shell shown",
   "players": [
    {
     "id": "oWR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "ghost": true,
     "role": "Wide Receiver"
    },
    {
     "id": "oWR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "ghost": true,
     "role": "Wide Receiver"
    },
    {
     "id": "oSL",
     "label": "SL",
     "x": 80,
     "y": 48,
     "ghost": true,
     "role": "Slot Receiver"
    },
    {
     "id": "oTE",
     "label": "TE",
     "x": 24,
     "y": 50,
     "ghost": true,
     "role": "Tight End"
    },
    {
     "id": "oRB",
     "label": "RB",
     "x": 50,
     "y": 58,
     "ghost": true,
     "role": "Running Back"
    },
    {
     "id": "CB1",
     "label": "CB",
     "x": 8,
     "y": 26,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Zone-turns-man: plays a deep quarter zone pre-snap, but locks onto a receiver who threatens it vertically."
    },
    {
     "id": "CB2",
     "label": "CB",
     "x": 92,
     "y": 26,
     "role": "Cornerback",
     "position_ref": "POSITION_CORNERBACK",
     "assignment": "Zone-turns-man on a vertical release."
    },
    {
     "id": "NB",
     "label": "NB",
     "x": 80,
     "y": 40,
     "role": "Nickel / Star",
     "position_ref": "POSITION_NICKEL_STAR",
     "assignment": "Pattern-reads the slot's release before deciding man or zone rules."
    },
    {
     "id": "LB1",
     "label": "LB",
     "x": 34,
     "y": 36,
     "role": "Will Linebacker",
     "position_ref": "POSITION_WILL_LINEBACKER",
     "assignment": "Underneath zone with man-match rules vs. a back releasing into his area."
    },
    {
     "id": "LB2",
     "label": "LB",
     "x": 50,
     "y": 36,
     "role": "Mike Linebacker",
     "position_ref": "POSITION_MIKE_LINEBACKER",
     "assignment": "Underneath zone with man-match rules."
    },
    {
     "id": "FS",
     "label": "FS",
     "x": 30,
     "y": 14,
     "role": "Free Safety",
     "position_ref": "POSITION_FREE_SAFETY",
     "assignment": "Deep quarter, matches vertical routes into man coverage."
    },
    {
     "id": "SS",
     "label": "SS",
     "x": 70,
     "y": 14,
     "role": "Strong Safety",
     "position_ref": "POSITION_STRONG_SAFETY",
     "assignment": "Deep quarter, matches vertical routes into man coverage."
    }
   ],
   "zones": [
    {
     "label": "Deep Quarter (matches verticals)",
     "cx": 12,
     "cy": 11,
     "rx": 14,
     "ry": 8
    },
    {
     "label": "Deep Quarter (matches verticals)",
     "cx": 88,
     "cy": 11,
     "rx": 14,
     "ry": 8
    }
   ],
   "weaknesses": "The pre-snap look reads like a zone shell, so it defends both man and zone beaters -- but the pattern-read rules that make it work are complex, and a blown rule creates the same busted-coverage explosive play as man or zone.",
   "description": "Match Coverage: defenders start in zone drops but convert to man rules once a receiver's route threatens their zone -- a hybrid of zone principles and man technique."
  }
 },
 "passConcepts": {
  "PASSCONCEPT_MESH": {
   "id": "PASSCONCEPT_MESH",
   "side": "offense",
   "los_y": 50,
   "category": "pass_concept",
   "verified": true,
   "display_name": "Mesh",
   "read": "High-low/rub read underneath",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 63,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 40,
     "y": 62,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "WR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "role": "Z Receiver",
     "position_ref": "POSITION_Z_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "SL1",
     "label": "SL",
     "x": 20,
     "y": 48,
     "role": "Slot / F Receiver",
     "position_ref": "POSITION_SLOT_F_RECEIVER",
     "assignment": "Works the middle of the field; frequent option/RPO read."
    },
    {
     "id": "SL2",
     "label": "SL",
     "x": 80,
     "y": 48,
     "role": "Slot / F Receiver",
     "position_ref": "POSITION_SLOT_F_RECEIVER",
     "assignment": "Works the middle of the field; frequent option/RPO read."
    }
   ],
   "routes": [
    {
     "player": "SL1",
     "points": [
      {
       "x": 20,
       "y": 50
      },
      {
       "x": 68,
       "y": 56
      },
      {
       "x": 78,
       "y": 56
      }
     ],
     "label": "Shallow cross"
    },
    {
     "player": "SL2",
     "points": [
      {
       "x": 80,
       "y": 50
      },
      {
       "x": 32,
       "y": 58
      },
      {
       "x": 22,
       "y": 58
      }
     ],
     "label": "Shallow cross (under)"
    },
    {
     "player": "WR1",
     "points": [
      {
       "x": 6,
       "y": 50
      },
      {
       "x": 6,
       "y": 26
      }
     ],
     "label": "Go / clear-out"
    },
    {
     "player": "WR2",
     "points": [
      {
       "x": 94,
       "y": 50
      },
      {
       "x": 94,
       "y": 26
      }
     ],
     "label": "Go / clear-out"
    },
    {
     "player": "RB",
     "points": [
      {
       "x": 40,
       "y": 62
      },
      {
       "x": 40,
       "y": 54
      }
     ]
    }
   ],
   "coverage_stress": "Man coverage in particular -- the two shallow crossers run at each other and naturally rub/pick defenders trailing in man.",
   "qb_read": "High-low the two crossers underneath; the deep clear-out routes hold the safeties off.",
   "weakness": "Zone defenders who pass off the crossers (rather than running into each other in man) take away the natural rub.",
   "description": "Mesh: two receivers cross shallow underneath at the same depth, with two vertical routes clearing out the deep defenders."
  },
  "PASSCONCEPT_FOUR_VERTICALS": {
   "id": "PASSCONCEPT_FOUR_VERTICALS",
   "side": "offense",
   "los_y": 50,
   "category": "pass_concept",
   "verified": true,
   "display_name": "Four Verticals",
   "read": "Vertical stretch, hole-shot read",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 63,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 40,
     "y": 62,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "WR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "role": "Z Receiver",
     "position_ref": "POSITION_Z_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "SL1",
     "label": "SL",
     "x": 26,
     "y": 50,
     "role": "Slot / F Receiver",
     "position_ref": "POSITION_SLOT_F_RECEIVER",
     "assignment": "Works the middle of the field; frequent option/RPO read."
    },
    {
     "id": "SL2",
     "label": "SL",
     "x": 74,
     "y": 50,
     "role": "Slot / F Receiver",
     "position_ref": "POSITION_SLOT_F_RECEIVER",
     "assignment": "Works the middle of the field; frequent option/RPO read."
    }
   ],
   "routes": [
    {
     "player": "WR1",
     "points": [
      {
       "x": 6,
       "y": 50
      },
      {
       "x": 6,
       "y": 20
      }
     ],
     "label": "Go"
    },
    {
     "player": "WR2",
     "points": [
      {
       "x": 94,
       "y": 50
      },
      {
       "x": 94,
       "y": 20
      }
     ],
     "label": "Go"
    },
    {
     "player": "SL1",
     "points": [
      {
       "x": 26,
       "y": 50
      },
      {
       "x": 32,
       "y": 20
      }
     ],
     "label": "Seam"
    },
    {
     "player": "SL2",
     "points": [
      {
       "x": 74,
       "y": 50
      },
      {
       "x": 68,
       "y": 20
      }
     ],
     "label": "Seam"
    }
   ],
   "coverage_stress": "Single-high (Cover 1/3) shells -- four vertical routes leave only one deep defender to cover the middle seams.",
   "qb_read": "Read the middle-of-field safety; throw the seam he doesn't get to.",
   "weakness": "Two-high shells (Cover 2/4) have enough deep defenders to match all four verticals without a hole.",
   "description": "Four Verticals: all four eligible receivers run vertical routes at once, stretching every deep defender."
  },
  "PASSCONCEPT_Y_CROSS": {
   "id": "PASSCONCEPT_Y_CROSS",
   "side": "offense",
   "los_y": 50,
   "category": "pass_concept",
   "verified": true,
   "display_name": "Y-Cross",
   "read": "Deep-cross progression",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "TE",
     "label": "TE",
     "x": 24,
     "y": 50,
     "role": "Tight End",
     "position_ref": "POSITION_TIGHT_END_Y",
     "assignment": "In-line blocker or short/intermediate receiving option."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 63,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 58,
     "y": 62,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "WR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "role": "Z Receiver",
     "position_ref": "POSITION_Z_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "SL1",
     "label": "SL",
     "x": 80,
     "y": 48,
     "role": "Slot / F Receiver",
     "position_ref": "POSITION_SLOT_F_RECEIVER",
     "assignment": "Works the middle of the field; frequent option/RPO read."
    }
   ],
   "routes": [
    {
     "player": "TE",
     "points": [
      {
       "x": 24,
       "y": 50
      },
      {
       "x": 55,
       "y": 34
      },
      {
       "x": 90,
       "y": 32
      }
     ],
     "label": "Deep cross"
    },
    {
     "player": "WR2",
     "points": [
      {
       "x": 94,
       "y": 50
      },
      {
       "x": 94,
       "y": 28
      }
     ],
     "label": "Go / hold the safety"
    },
    {
     "player": "SL1",
     "points": [
      {
       "x": 80,
       "y": 50
      },
      {
       "x": 80,
       "y": 40
      },
      {
       "x": 68,
       "y": 40
      }
     ],
     "label": "Dig"
    },
    {
     "player": "WR1",
     "points": [
      {
       "x": 6,
       "y": 50
      },
      {
       "x": 6,
       "y": 54
      },
      {
       "x": 14,
       "y": 54
      }
     ],
     "label": "Drag / checkdown"
    }
   ],
   "coverage_stress": "Attacks the middle of the field behind the linebackers -- especially effective vs. single-high coverage that has to run with the crosser.",
   "qb_read": "Deep cross first, working back to the dig, then the drag as the checkdown.",
   "weakness": "A robber or rat defender sitting in the crosser's path can undercut the route before it clears the linebackers.",
   "description": "Y-Cross: the tight end runs a deep crossing route from one side of the formation all the way to the other, with routes underneath and over the top to hold defenders."
  },
  "PASSCONCEPT_FLOOD": {
   "id": "PASSCONCEPT_FLOOD",
   "side": "offense",
   "los_y": 50,
   "category": "pass_concept",
   "verified": true,
   "display_name": "Flood",
   "read": "High-low-low to one side",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 26,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 35,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 44,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 53,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 62,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 44,
     "y": 63,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 56,
     "y": 62,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 8,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "WR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "role": "Z Receiver",
     "position_ref": "POSITION_Z_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "SL1",
     "label": "SL",
     "x": 82,
     "y": 48,
     "role": "Slot / F Receiver",
     "position_ref": "POSITION_SLOT_F_RECEIVER",
     "assignment": "Works the middle of the field; frequent option/RPO read."
    }
   ],
   "routes": [
    {
     "player": "WR2",
     "points": [
      {
       "x": 94,
       "y": 50
      },
      {
       "x": 94,
       "y": 28
      }
     ],
     "label": "Go (clears deep)"
    },
    {
     "player": "SL1",
     "points": [
      {
       "x": 82,
       "y": 50
      },
      {
       "x": 82,
       "y": 40
      }
     ],
     "label": "Out/comeback (intermediate)"
    },
    {
     "player": "RB",
     "points": [
      {
       "x": 56,
       "y": 62
      },
      {
       "x": 74,
       "y": 53
      }
     ],
     "label": "Flat (short)"
    }
   ],
   "coverage_stress": "Three receivers stacked at three depths in the same third of the field overload any single zone defender to that side.",
   "qb_read": "High-low-low, outside in: deep clears space, intermediate sits in the window it opens, flat is the built-in checkdown.",
   "weakness": "A team that rotates two defenders (not just one) to the flooded side can match all three levels.",
   "description": "Flood: three receivers to one side of the formation run routes at three different depths -- deep, intermediate, and flat."
  },
  "PASSCONCEPT_LEVELS": {
   "id": "PASSCONCEPT_LEVELS",
   "side": "offense",
   "los_y": 50,
   "category": "pass_concept",
   "verified": true,
   "display_name": "Levels",
   "read": "In-breaking horizontal stretch",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 63,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 40,
     "y": 62,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "WR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "role": "Z Receiver",
     "position_ref": "POSITION_Z_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "SL1",
     "label": "SL",
     "x": 80,
     "y": 48,
     "role": "Slot / F Receiver",
     "position_ref": "POSITION_SLOT_F_RECEIVER",
     "assignment": "Works the middle of the field; frequent option/RPO read."
    }
   ],
   "routes": [
    {
     "player": "WR2",
     "points": [
      {
       "x": 94,
       "y": 50
      },
      {
       "x": 94,
       "y": 42
      },
      {
       "x": 60,
       "y": 42
      }
     ],
     "label": "Deep in (12-14 yd)"
    },
    {
     "player": "SL1",
     "points": [
      {
       "x": 80,
       "y": 50
      },
      {
       "x": 80,
       "y": 46
      },
      {
       "x": 55,
       "y": 46
      }
     ],
     "label": "Shallow in (5-6 yd)"
    }
   ],
   "coverage_stress": "Stacks two in-breaking routes at different depths on the same side, both working against the same zone defender's leverage.",
   "qb_read": "Read the underneath zone defender -- if he sits on the shallow in, throw the deep in behind him; if he carries the deep one, the shallow is open.",
   "weakness": "Two defenders (rather than one carrying both levels) can split the routes evenly.",
   "description": "Levels: two receivers on the same side run in-breaking routes at two different depths, creating a simple horizontal read for the quarterback."
  },
  "PASSCONCEPT_STICK": {
   "id": "PASSCONCEPT_STICK",
   "side": "offense",
   "los_y": 50,
   "category": "pass_concept",
   "verified": true,
   "display_name": "Stick",
   "read": "Quick, sideline triangle read",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "TE",
     "label": "TE",
     "x": 76,
     "y": 50,
     "role": "Tight End",
     "position_ref": "POSITION_TIGHT_END_Y",
     "assignment": "In-line blocker or short/intermediate receiving option."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 54,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 40,
     "y": 60,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "WR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "role": "Z Receiver",
     "position_ref": "POSITION_Z_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    }
   ],
   "routes": [
    {
     "player": "TE",
     "points": [
      {
       "x": 76,
       "y": 50
      },
      {
       "x": 76,
       "y": 44
      }
     ],
     "label": "Stick (sits down at 5-6 yd)"
    },
    {
     "player": "WR2",
     "points": [
      {
       "x": 94,
       "y": 50
      },
      {
       "x": 94,
       "y": 46
      },
      {
       "x": 86,
       "y": 42
      }
     ],
     "label": "Flat/corner (outside leverage)"
    },
    {
     "player": "RB",
     "points": [
      {
       "x": 40,
       "y": 60
      },
      {
       "x": 58,
       "y": 52
      }
     ]
    }
   ],
   "coverage_stress": "A quick-game triangle to one side -- gives the quarterback a fast, high-percentage answer to almost any coverage.",
   "qb_read": "Pre- or post-snap leverage read: if the flat defender widens, throw the stick underneath him; if he sits inside, throw the flat.",
   "weakness": "Disciplined underneath zone defenders who split the difference between the two short routes can take both away on a given rep.",
   "description": "Stick: a tight end or slot sits down in a short hook while a receiver works the flat outside him, giving a fast horizontal read."
  },
  "PASSCONCEPT_DRIVE": {
   "id": "PASSCONCEPT_DRIVE",
   "side": "offense",
   "los_y": 50,
   "category": "pass_concept",
   "verified": true,
   "display_name": "Drive",
   "read": "Shallow/dig combination",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "TE",
     "label": "TE",
     "x": 24,
     "y": 50,
     "role": "Tight End",
     "position_ref": "POSITION_TIGHT_END_Y",
     "assignment": "In-line blocker or short/intermediate receiving option."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 63,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 58,
     "y": 62,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "WR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "role": "Z Receiver",
     "position_ref": "POSITION_Z_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    }
   ],
   "routes": [
    {
     "player": "WR1",
     "points": [
      {
       "x": 6,
       "y": 50
      },
      {
       "x": 30,
       "y": 53
      },
      {
       "x": 60,
       "y": 53
      }
     ],
     "label": "Shallow cross"
    },
    {
     "player": "TE",
     "points": [
      {
       "x": 24,
       "y": 50
      },
      {
       "x": 24,
       "y": 38
      },
      {
       "x": 50,
       "y": 38
      }
     ],
     "label": "Dig (behind the shallow)"
    },
    {
     "player": "WR2",
     "points": [
      {
       "x": 94,
       "y": 50
      },
      {
       "x": 94,
       "y": 28
      }
     ],
     "label": "Go / clear-out"
    }
   ],
   "coverage_stress": "Combines a very shallow drive route with a deeper dig from the other side, working the same underneath-to-intermediate window from opposite directions.",
   "qb_read": "Shallow first (usually open quickly against most zone/man rules), climbing to the dig behind it if the shallow is taken away.",
   "weakness": "A trailing man defender who stays in the shallow receiver's hip pocket can force the ball elsewhere before the dig sits down.",
   "description": "Drive: a very shallow crossing route paired with a deeper dig route from the opposite side, working the same area at two depths."
  },
  "PASSCONCEPT_SMASH": {
   "id": "PASSCONCEPT_SMASH",
   "side": "offense",
   "los_y": 50,
   "category": "pass_concept",
   "verified": true,
   "display_name": "Smash",
   "read": "Corner/hitch high-low",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 63,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 40,
     "y": 62,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "WR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "role": "Z Receiver",
     "position_ref": "POSITION_Z_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "SL1",
     "label": "SL",
     "x": 80,
     "y": 48,
     "role": "Slot / F Receiver",
     "position_ref": "POSITION_SLOT_F_RECEIVER",
     "assignment": "Works the middle of the field; frequent option/RPO read."
    }
   ],
   "routes": [
    {
     "player": "WR2",
     "points": [
      {
       "x": 94,
       "y": 50
      },
      {
       "x": 94,
       "y": 46
      }
     ],
     "label": "Hitch (short, outside)"
    },
    {
     "player": "SL1",
     "points": [
      {
       "x": 80,
       "y": 50
      },
      {
       "x": 80,
       "y": 40
      },
      {
       "x": 94,
       "y": 34
      }
     ],
     "label": "Corner (deep, outside)"
    }
   ],
   "coverage_stress": "Classic Cover 2 beater -- stacks a short hitch under a deep corner route to the same side, the exact two levels a Cover 2 corner and safety split.",
   "qb_read": "Read the flat/corner defender: if he stays low on the hitch, throw the corner over him; if he carries the corner, the hitch is open underneath.",
   "weakness": "A safety who rotates over quickly, or a corner playing further off, can shrink the window the corner route needs.",
   "description": "Smash: a short outside hitch route paired with a deeper corner route from a receiver stacked inside it -- a two-level stretch on one defender."
  },
  "PASSCONCEPT_SLANT_FLAT": {
   "id": "PASSCONCEPT_SLANT_FLAT",
   "side": "offense",
   "los_y": 50,
   "category": "pass_concept",
   "verified": true,
   "display_name": "Slants",
   "read": "Slant/flat high-low, quick game",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 63,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 40,
     "y": 62,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "WR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "role": "Z Receiver",
     "position_ref": "POSITION_Z_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "SL1",
     "label": "SL",
     "x": 80,
     "y": 48,
     "role": "Slot / F Receiver",
     "position_ref": "POSITION_SLOT_F_RECEIVER",
     "assignment": "Works the middle of the field; frequent option/RPO read."
    }
   ],
   "routes": [
    {
     "player": "WR2",
     "points": [
      {
       "x": 94,
       "y": 50
      },
      {
       "x": 86,
       "y": 45
      }
     ],
     "label": "Slant"
    },
    {
     "player": "SL1",
     "points": [
      {
       "x": 80,
       "y": 50
      },
      {
       "x": 80,
       "y": 48
      },
      {
       "x": 90,
       "y": 48
      }
     ],
     "label": "Flat"
    }
   ],
   "coverage_stress": "A fast, timing-based quick-game answer to off coverage and most zone looks -- the ball is out before the pass rush is a factor.",
   "qb_read": "Pre-snap leverage/coverage read, then a quick, rhythm throw -- if the corner plays outside leverage or soft, the slant is the answer; the flat is the built-in checkdown.",
   "weakness": "Press man coverage that reroutes the slant receiver at the line can disrupt the route's timing before it starts.",
   "description": "Slants: an inside-breaking slant route paired with an underneath flat route, thrown quickly off a pre-snap leverage read."
  },
  "PASSCONCEPT_HANK_CURL_FLAT": {
   "id": "PASSCONCEPT_HANK_CURL_FLAT",
   "side": "offense",
   "los_y": 50,
   "category": "pass_concept",
   "verified": true,
   "display_name": "Curl/Flat",
   "read": "Curl-flat high-low",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "TE",
     "label": "TE",
     "x": 76,
     "y": 50,
     "role": "Tight End",
     "position_ref": "POSITION_TIGHT_END_Y",
     "assignment": "In-line blocker or short/intermediate receiving option."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 54,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 40,
     "y": 60,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "WR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "role": "Z Receiver",
     "position_ref": "POSITION_Z_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    }
   ],
   "routes": [
    {
     "player": "WR2",
     "points": [
      {
       "x": 94,
       "y": 50
      },
      {
       "x": 94,
       "y": 38
      },
      {
       "x": 88,
       "y": 36
      }
     ],
     "label": "Curl (sits down ~12-14 yd)"
    },
    {
     "player": "TE",
     "points": [
      {
       "x": 76,
       "y": 50
      },
      {
       "x": 86,
       "y": 47
      }
     ],
     "label": "Flat"
    }
   ],
   "coverage_stress": "Puts the same flat defender in conflict between a short flat route and a curl sitting down behind him -- one of the most common quick-game reads in football.",
   "qb_read": "If the flat defender jumps the flat route, throw the curl behind him; if he sinks with the curl, the flat is open.",
   "weakness": "A pattern-match defender who reads the release rather than reacting late can stay in position for both.",
   "description": "Curl/Flat: a receiver sits down in a curl behind a route working the flat underneath him, putting one defender in conflict between the two."
  },
  "PASSCONCEPT_SNAG": {
   "id": "PASSCONCEPT_SNAG",
   "side": "offense",
   "los_y": 50,
   "category": "pass_concept",
   "verified": true,
   "display_name": "Snag",
   "read": "Corner/snag/flat triangle",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 63,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 40,
     "y": 62,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 6,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "WR2",
     "label": "WR",
     "x": 94,
     "y": 50,
     "role": "Z Receiver",
     "position_ref": "POSITION_Z_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    },
    {
     "id": "SL1",
     "label": "SL",
     "x": 80,
     "y": 48,
     "role": "Slot / F Receiver",
     "position_ref": "POSITION_SLOT_F_RECEIVER",
     "assignment": "Works the middle of the field; frequent option/RPO read."
    }
   ],
   "routes": [
    {
     "player": "WR2",
     "points": [
      {
       "x": 94,
       "y": 50
      },
      {
       "x": 94,
       "y": 40
      },
      {
       "x": 86,
       "y": 34
      }
     ],
     "label": "Corner (deep, outside)"
    },
    {
     "player": "SL1",
     "points": [
      {
       "x": 80,
       "y": 50
      },
      {
       "x": 80,
       "y": 44
      },
      {
       "x": 70,
       "y": 44
      }
     ],
     "label": "Snag (short hook, inside)"
    },
    {
     "player": "RB",
     "points": [
      {
       "x": 40,
       "y": 62
      },
      {
       "x": 60,
       "y": 53
      }
     ],
     "label": "Flat"
    }
   ],
   "coverage_stress": "A three-level triangle to one side (corner, snag, flat) -- very similar shape to Smash/Stick but with the snag replacing the hitch.",
   "qb_read": "High-low-low outside in, same as Flood -- corner clears, snag sits in the window, flat is the checkdown.",
   "weakness": "Coverage that rotates two defenders to the triangle side rather than one can match all three levels.",
   "description": "Snag: a deep corner route clears out space for a short inside hook (the \"snag\") with a flat route underneath as a checkdown."
  }
 },
 "runConcepts": {
  "RUN_INSIDE_ZONE": {
   "id": "RUN_INSIDE_ZONE",
   "side": "offense",
   "los_y": 50,
   "category": "run_concept",
   "verified": true,
   "display_name": "Inside Zone",
   "gap": "Playside A/B gap, zone-blocked",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "TE",
     "label": "TE",
     "x": 76,
     "y": 50,
     "role": "Tight End",
     "position_ref": "POSITION_TIGHT_END_Y",
     "assignment": "In-line blocker or short/intermediate receiving option."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 63,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 42,
     "y": 62,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    }
   ],
   "blocks": [
    {
     "player": "RT",
     "points": [
      {
       "x": 68,
       "y": 50
      },
      {
       "x": 66,
       "y": 48
      }
     ]
    },
    {
     "player": "RG",
     "points": [
      {
       "x": 59,
       "y": 50
      },
      {
       "x": 56,
       "y": 48
      }
     ]
    },
    {
     "player": "C",
     "points": [
      {
       "x": 50,
       "y": 50
      },
      {
       "x": 52,
       "y": 49
      }
     ]
    },
    {
     "player": "LG",
     "points": [
      {
       "x": 41,
       "y": 50
      },
      {
       "x": 44,
       "y": 49
      }
     ]
    },
    {
     "player": "LT",
     "points": [
      {
       "x": 32,
       "y": 50
      },
      {
       "x": 36,
       "y": 49
      }
     ]
    },
    {
     "player": "TE",
     "points": [
      {
       "x": 76,
       "y": 50
      },
      {
       "x": 70,
       "y": 49
      }
     ]
    }
   ],
   "ball_path": [
    {
     "x": 42,
     "y": 62
    },
    {
     "x": 50,
     "y": 53
    },
    {
     "x": 54,
     "y": 42
    }
   ],
   "assignment_summary": "Every lineman blocks the play side, working double teams up to the second level -- the back reads the first down lineman past the center and picks a lane (\"bang, bend, or bounce\").",
   "weakness": "A well-fit backside defender or a linebacker who scrapes over the top before the double team's second-level release can spill the run outside the intended lane.",
   "description": "Inside Zone: the entire offensive line steps and blocks playside as a unit, and the running back reads the resulting movement to pick his lane."
  },
  "RUN_WIDE_ZONE": {
   "id": "RUN_WIDE_ZONE",
   "side": "offense",
   "los_y": 50,
   "category": "run_concept",
   "verified": true,
   "display_name": "Outside/Wide Zone",
   "gap": "Perimeter, zone-blocked",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "TE",
     "label": "TE",
     "x": 76,
     "y": 50,
     "role": "Tight End",
     "position_ref": "POSITION_TIGHT_END_Y",
     "assignment": "In-line blocker or short/intermediate receiving option."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 63,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 36,
     "y": 61,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    }
   ],
   "blocks": [
    {
     "player": "RT",
     "points": [
      {
       "x": 68,
       "y": 50
      },
      {
       "x": 78,
       "y": 49
      }
     ]
    },
    {
     "player": "RG",
     "points": [
      {
       "x": 59,
       "y": 50
      },
      {
       "x": 68,
       "y": 49
      }
     ]
    },
    {
     "player": "C",
     "points": [
      {
       "x": 50,
       "y": 50
      },
      {
       "x": 58,
       "y": 49
      }
     ]
    },
    {
     "player": "LG",
     "points": [
      {
       "x": 41,
       "y": 50
      },
      {
       "x": 48,
       "y": 49
      }
     ]
    },
    {
     "player": "LT",
     "points": [
      {
       "x": 32,
       "y": 50
      },
      {
       "x": 38,
       "y": 49
      }
     ]
    },
    {
     "player": "TE",
     "points": [
      {
       "x": 76,
       "y": 50
      },
      {
       "x": 86,
       "y": 49
      }
     ]
    }
   ],
   "ball_path": [
    {
     "x": 36,
     "y": 61
    },
    {
     "x": 66,
     "y": 54
    },
    {
     "x": 82,
     "y": 46
    }
   ],
   "assignment_summary": "The whole line takes a lateral zone step toward the perimeter before climbing -- the back presses the sideline and can cut all the way back if the defense overruns it. Widely called \"stretch\" in many playbooks -- same concept, different name.",
   "weakness": "Elite backside pursuit or a defender who stays home rather than chasing the flow can run the play down from behind.",
   "description": "Outside/Wide Zone: the line steps laterally toward the perimeter, and the back presses the edge before deciding whether to bounce outside or cut back."
  },
  "RUN_POWER": {
   "id": "RUN_POWER",
   "side": "offense",
   "los_y": 50,
   "category": "run_concept",
   "verified": true,
   "display_name": "Power",
   "gap": "Playside gap, gap-blocked with a puller",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "TE",
     "label": "TE",
     "x": 76,
     "y": 50,
     "role": "Tight End",
     "position_ref": "POSITION_TIGHT_END_Y",
     "assignment": "In-line blocker or short/intermediate receiving option."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 54,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "FB",
     "label": "FB",
     "x": 50,
     "y": 58,
     "role": "Fullback",
     "position_ref": "POSITION_FULLBACK",
     "assignment": "Lead blocker; occasional short-yardage carrier."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 50,
     "y": 66,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    }
   ],
   "blocks": [
    {
     "player": "RT",
     "points": [
      {
       "x": 68,
       "y": 50
      },
      {
       "x": 70,
       "y": 47
      }
     ]
    },
    {
     "player": "RG",
     "points": [
      {
       "x": 59,
       "y": 50
      },
      {
       "x": 62,
       "y": 47
      }
     ]
    },
    {
     "player": "C",
     "points": [
      {
       "x": 50,
       "y": 50
      },
      {
       "x": 55,
       "y": 48
      }
     ]
    },
    {
     "player": "LG",
     "points": [
      {
       "x": 41,
       "y": 50
      },
      {
       "x": 66,
       "y": 45
      }
     ],
     "label": "Pulls and leads through the hole"
    },
    {
     "player": "TE",
     "points": [
      {
       "x": 76,
       "y": 50
      },
      {
       "x": 72,
       "y": 48
      }
     ]
    },
    {
     "player": "FB",
     "points": [
      {
       "x": 50,
       "y": 58
      },
      {
       "x": 66,
       "y": 49
      }
     ],
     "label": "Lead blocks the edge defender"
    }
   ],
   "ball_path": [
    {
     "x": 50,
     "y": 66
    },
    {
     "x": 58,
     "y": 54
    },
    {
     "x": 68,
     "y": 44
    }
   ],
   "assignment_summary": "Playside double-teams the point of attack while the backside guard pulls around to lead through the hole, with a fullback or lead blocker kicking out the edge defender.",
   "weakness": "A defender who reads the pulling guard quickly and scrapes to fill the hole before the puller arrives can blow the play up in the backfield.",
   "description": "Power: playside double team at the point of attack, backside guard pulls to lead through the hole, fullback kicks out the edge defender."
  },
  "RUN_COUNTER_GT": {
   "id": "RUN_COUNTER_GT",
   "side": "offense",
   "los_y": 50,
   "category": "run_concept",
   "verified": true,
   "display_name": "Counter GT",
   "gap": "Playside gap, misdirection with two pullers",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "TE",
     "label": "TE",
     "x": 76,
     "y": 50,
     "role": "Tight End",
     "position_ref": "POSITION_TIGHT_END_Y",
     "assignment": "In-line blocker or short/intermediate receiving option."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 63,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 60,
     "y": 62,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    }
   ],
   "blocks": [
    {
     "player": "RT",
     "points": [
      {
       "x": 68,
       "y": 50
      },
      {
       "x": 66,
       "y": 47
      }
     ]
    },
    {
     "player": "TE",
     "points": [
      {
       "x": 76,
       "y": 50
      },
      {
       "x": 72,
       "y": 48
      }
     ]
    },
    {
     "player": "RG",
     "points": [
      {
       "x": 59,
       "y": 50
      },
      {
       "x": 36,
       "y": 46
      }
     ],
     "label": "Pulls to kick out the edge"
    },
    {
     "player": "LT",
     "points": [
      {
       "x": 32,
       "y": 50
      },
      {
       "x": 30,
       "y": 48
      }
     ]
    },
    {
     "player": "LG",
     "points": [
      {
       "x": 41,
       "y": 50
      },
      {
       "x": 30,
       "y": 45
      }
     ],
     "label": "Pulls to lead through the hole"
    }
   ],
   "ball_path": [
    {
     "x": 60,
     "y": 62
    },
    {
     "x": 48,
     "y": 55
    },
    {
     "x": 34,
     "y": 44
    }
   ],
   "assignment_summary": "The back opens showing playside flow, then the ball is run to the opposite side behind two pulling linemen (\"guard-tackle\" or \"guard-guard,\" depending on the scheme) -- the counter step is what makes it misdirection.",
   "weakness": "A disciplined backside end/linebacker who doesn't bite on the initial flow can sit and read the counter developing.",
   "description": "Counter GT: the running back's first step shows flow one way before the ball is run behind two pulling linemen to the other side."
  },
  "RUN_DUO": {
   "id": "RUN_DUO",
   "side": "offense",
   "los_y": 50,
   "category": "run_concept",
   "verified": true,
   "display_name": "Duo",
   "gap": "Playside double teams, downhill",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "TE",
     "label": "TE",
     "x": 76,
     "y": 50,
     "role": "Tight End",
     "position_ref": "POSITION_TIGHT_END_Y",
     "assignment": "In-line blocker or short/intermediate receiving option."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 63,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 42,
     "y": 62,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    }
   ],
   "blocks": [
    {
     "player": "RT",
     "points": [
      {
       "x": 68,
       "y": 50
      },
      {
       "x": 67,
       "y": 47
      }
     ]
    },
    {
     "player": "RG",
     "points": [
      {
       "x": 59,
       "y": 50
      },
      {
       "x": 58,
       "y": 47
      }
     ]
    },
    {
     "player": "C",
     "points": [
      {
       "x": 50,
       "y": 50
      },
      {
       "x": 51,
       "y": 47
      }
     ]
    },
    {
     "player": "LG",
     "points": [
      {
       "x": 41,
       "y": 50
      },
      {
       "x": 42,
       "y": 47
      }
     ]
    }
   ],
   "ball_path": [
    {
     "x": 42,
     "y": 62
    },
    {
     "x": 48,
     "y": 52
    },
    {
     "x": 52,
     "y": 42
    }
   ],
   "assignment_summary": "Often called \"man-in schemed like zone\" -- double teams straight upfield at the point of attack with no pullers, letting the back press one hole and get downhill fast.",
   "weakness": "A linebacker who fills the single gap the scheme is designed to hit before the double team climbs to the second level can limit the play to a short gain.",
   "description": "Duo: two double teams straight ahead at the point of attack, a simple, downhill, one-read run for the back."
  },
  "RUN_TRAP": {
   "id": "RUN_TRAP",
   "side": "offense",
   "los_y": 50,
   "category": "run_concept",
   "verified": true,
   "display_name": "Trap",
   "gap": "Interior gap, puller traps a penetrating lineman",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 54,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 50,
     "y": 65,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    }
   ],
   "blocks": [
    {
     "player": "RG",
     "points": [
      {
       "x": 59,
       "y": 50
      },
      {
       "x": 46,
       "y": 48
      }
     ],
     "label": "Pulls to trap the unblocked defender"
    },
    {
     "player": "LT",
     "points": [
      {
       "x": 32,
       "y": 50
      },
      {
       "x": 34,
       "y": 48
      }
     ]
    },
    {
     "player": "LG",
     "points": [
      {
       "x": 41,
       "y": 50
      },
      {
       "x": 38,
       "y": 47
      }
     ]
    }
   ],
   "ball_path": [
    {
     "x": 50,
     "y": 65
    },
    {
     "x": 48,
     "y": 54
    },
    {
     "x": 44,
     "y": 44
    }
   ],
   "assignment_summary": "A defensive lineman is deliberately left unblocked to penetrate upfield, then a pulling guard blocks (\"traps\") him from the side -- the back reads the trap block and runs off it.",
   "weakness": "A defender who reads the trap and squeezes down rather than continuing to penetrate can beat the puller to the spot.",
   "description": "Trap: one defensive lineman is left unblocked on purpose so he penetrates upfield, then a pulling guard blocks him from the side."
  },
  "RUN_TOSS_CRACK_TOSS": {
   "id": "RUN_TOSS_CRACK_TOSS",
   "side": "offense",
   "los_y": 50,
   "category": "run_concept",
   "verified": true,
   "display_name": "Toss / Crack Toss",
   "gap": "Perimeter, pitched to the back",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 63,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 30,
     "y": 60,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    },
    {
     "id": "WR1",
     "label": "WR",
     "x": 8,
     "y": 50,
     "role": "X Receiver",
     "position_ref": "POSITION_X_RECEIVER",
     "assignment": "Stretches the field vertically or works the perimeter."
    }
   ],
   "blocks": [
    {
     "player": "RT",
     "points": [
      {
       "x": 68,
       "y": 50
      },
      {
       "x": 74,
       "y": 48
      }
     ]
    },
    {
     "player": "WR1",
     "points": [
      {
       "x": 8,
       "y": 50
      },
      {
       "x": 18,
       "y": 47
      }
     ],
     "label": "Crack block on a defender inside"
    }
   ],
   "ball_path": [
    {
     "x": 30,
     "y": 60
    },
    {
     "x": 18,
     "y": 58
    },
    {
     "x": 10,
     "y": 48
    }
   ],
   "assignment_summary": "The ball is pitched or tossed immediately to a back attacking the perimeter, often paired with a receiver \"crack\" block on the force defender from the inside.",
   "weakness": "A force defender who sets the edge and doesn't get cracked, or fast pursuit from the backside, can limit the play before it turns the corner.",
   "description": "Toss / Crack Toss: the ball is pitched to the back attacking the edge immediately, often with a receiver crack-blocking a defender from the inside."
  },
  "RUN_DRAW": {
   "id": "RUN_DRAW",
   "side": "offense",
   "los_y": 50,
   "category": "run_concept",
   "verified": true,
   "display_name": "Draw",
   "gap": "Delayed, reactive to the rush",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 63,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 42,
     "y": 63,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    }
   ],
   "blocks": [
    {
     "player": "RT",
     "points": [
      {
       "x": 68,
       "y": 50
      },
      {
       "x": 67,
       "y": 49
      }
     ],
     "label": "Shows pass-set, then blocks down"
    },
    {
     "player": "RG",
     "points": [
      {
       "x": 59,
       "y": 50
      },
      {
       "x": 58,
       "y": 49
      }
     ]
    },
    {
     "player": "C",
     "points": [
      {
       "x": 50,
       "y": 50
      },
      {
       "x": 51,
       "y": 49
      }
     ]
    }
   ],
   "ball_path": [
    {
     "x": 42,
     "y": 63
    },
    {
     "x": 46,
     "y": 56
    },
    {
     "x": 52,
     "y": 46
    }
   ],
   "assignment_summary": "The offensive line shows pass protection to draw the defensive line upfield, then the back hits a lane created by the rushers' own momentum.",
   "weakness": "Disciplined rushers who maintain their rush lanes rather than getting too far upfield leave less room for the delayed hand-off to hit.",
   "description": "Draw: the line fakes pass protection to draw the rush upfield, and the back runs through the lane the rushers vacate."
  },
  "RUN_SWEEP": {
   "id": "RUN_SWEEP",
   "side": "offense",
   "los_y": 50,
   "category": "run_concept",
   "verified": true,
   "display_name": "Sweep",
   "gap": "Perimeter, pulling linemen lead",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 54,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 30,
     "y": 60,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    }
   ],
   "blocks": [
    {
     "player": "LG",
     "points": [
      {
       "x": 41,
       "y": 50
      },
      {
       "x": 20,
       "y": 48
      }
     ],
     "label": "Pulls and leads around the edge"
    },
    {
     "player": "RG",
     "points": [
      {
       "x": 59,
       "y": 50
      },
      {
       "x": 24,
       "y": 47
      }
     ],
     "label": "Pulls and leads around the edge"
    }
   ],
   "ball_path": [
    {
     "x": 30,
     "y": 60
    },
    {
     "x": 20,
     "y": 56
    },
    {
     "x": 14,
     "y": 47
    }
   ],
   "assignment_summary": "Both guards pull and lead the back around the edge -- more developing time than Toss, but two lead blockers to clear the perimeter.",
   "weakness": "Fast edge pursuit that beats the pullers to the corner, or a force defender who stays disciplined outside, can spill the play back inside into pursuit.",
   "description": "Sweep: both guards pull and lead the running back around the edge of the formation."
  },
  "RUN_ZONE_READ": {
   "id": "RUN_ZONE_READ",
   "side": "offense",
   "los_y": 50,
   "category": "run_concept",
   "verified": true,
   "display_name": "Zone Read (Read Option)",
   "gap": "Backside, QB-read option",
   "players": [
    {
     "id": "LT",
     "label": "LT",
     "x": 32,
     "y": 50,
     "role": "Left Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the QB's blind side or drives the edge on run plays."
    },
    {
     "id": "LG",
     "label": "LG",
     "x": 41,
     "y": 50,
     "role": "Left Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "C",
     "label": "C",
     "x": 50,
     "y": 50,
     "role": "Center",
     "position_ref": "POSITION_CENTER",
     "assignment": "Snaps the ball; makes protection/run calls for the line."
    },
    {
     "id": "RG",
     "label": "RG",
     "x": 59,
     "y": 50,
     "role": "Right Guard",
     "position_ref": "POSITION_GUARD",
     "assignment": "Interior gap protection; pulls on power/counter schemes."
    },
    {
     "id": "RT",
     "label": "RT",
     "x": 68,
     "y": 50,
     "role": "Right Tackle",
     "position_ref": "POSITION_LEFT_RIGHT_TACKLE",
     "assignment": "Protects the edge on the strong/closed side."
    },
    {
     "id": "QB",
     "label": "QB",
     "x": 50,
     "y": 63,
     "role": "Quarterback",
     "position_ref": "POSITION_QUARTERBACK",
     "assignment": "Takes the snap and directs the play."
    },
    {
     "id": "RB",
     "label": "RB",
     "x": 40,
     "y": 61,
     "role": "Running Back",
     "position_ref": "POSITION_RUNNING_BACK",
     "assignment": "Primary ball carrier or pass-protection help."
    }
   ],
   "blocks": [
    {
     "player": "RT",
     "points": [
      {
       "x": 68,
       "y": 50
      },
      {
       "x": 66,
       "y": 48
      }
     ]
    },
    {
     "player": "RG",
     "points": [
      {
       "x": 59,
       "y": 50
      },
      {
       "x": 56,
       "y": 48
      }
     ]
    },
    {
     "player": "C",
     "points": [
      {
       "x": 50,
       "y": 50
      },
      {
       "x": 52,
       "y": 49
      }
     ]
    },
    {
     "player": "LG",
     "points": [
      {
       "x": 41,
       "y": 50
      },
      {
       "x": 44,
       "y": 49
      }
     ]
    }
   ],
   "ball_path": [
    {
     "x": 40,
     "y": 61
    },
    {
     "x": 48,
     "y": 54
    },
    {
     "x": 54,
     "y": 44
    }
   ],
   "note_unblocked": "The backside defensive end (near x=30) is left unblocked on purpose -- he is the QB's read key, not a blocking assignment.",
   "assignment_summary": "The line blocks inside zone while the backside end is deliberately left unblocked -- the quarterback reads that defender after the snap: hand off if he crashes down the line, keep it himself if he stays wide for the QB.",
   "weakness": "A disciplined end who plays the mesh point rather than committing hard either way (a \"scrape exchange\" behind him) can take away both options.",
   "description": "Zone Read: the offensive line blocks inside zone, and the quarterback reads the unblocked backside defender to decide whether to hand off or keep the ball himself."
  }
 }
};
