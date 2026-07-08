"""
patient_language.py
===================
Plain-English explanations for every body part + condition.
Written at a 6th-grade reading level — no medical jargon.

Each entry has:
  headline      – one-line summary (shown large)
  what_found    – what the AI saw in simple words
  what_it_means – what it means for your health
  what_to_do    – action the patient should take
  urgency       – "good" | "watch" | "soon" | "urgent"
  emoji         – visual indicator
"""

# ── Normal / Healthy fallback (used by all body parts) ───────────────────────

_NORMAL_TEMPLATE = {
    "headline": "Your {part} looks healthy",
    "what_found": (
        "The AI did not find any signs of disease or injury in your {part} X-ray. "
        "Everything appears to be within normal limits."
    ),
    "what_it_means": ("Based on this X-ray, your {part} looks healthy. " "That is great news!"),
    "what_to_do": (
        "No urgent action is needed. Keep up with your regular health check-ups "
        "and let your doctor know if you develop any new symptoms."
    ),
    "urgency": "good",
    "emoji": "✅",
}

# ── Condition-specific plain-English templates ────────────────────────────────

PATIENT_LANGUAGE: dict[str, dict[str, dict]] = {
    # ── CHEST ─────────────────────────────────────────────────────────────────
    "chest": {
        "Normal": {
            **_NORMAL_TEMPLATE,
            "headline": "Your lungs look healthy",
            "what_found": (
                "The AI did not find any signs of infection, fluid, or disease "
                "in your chest X-ray."
            ),
            "what_it_means": "Your lungs and heart appear to be in good shape.",
        },
        "Pneumonia": {
            "headline": "Possible lung infection detected",
            "what_found": (
                "The AI found patterns in your chest X-ray that look like "
                "pneumonia — an infection that causes the air sacs in your "
                "lungs to fill with fluid or pus."
            ),
            "what_it_means": (
                "Pneumonia can make breathing difficult and cause fever, cough, "
                "and chest pain. It usually needs treatment with medicine. "
                "The good news is that it is very treatable, especially when "
                "caught early."
            ),
            "what_to_do": (
                "Please see a doctor as soon as possible — ideally today or "
                "tomorrow. Your doctor will confirm the diagnosis and prescribe "
                "the right treatment, usually antibiotics or antiviral medicine."
            ),
            "urgency": "urgent",
            "emoji": "⚠️",
        },
    },
    # ── KNEE ──────────────────────────────────────────────────────────────────
    "knee": {
        "Normal": {**_NORMAL_TEMPLATE, "headline": "Your knee looks healthy"},
        "Osteoarthritis": {
            "headline": "Signs of knee wear and tear detected",
            "what_found": (
                "The AI spotted signs of osteoarthritis — a condition where "
                "the cartilage (the cushioning between your knee bones) has "
                "worn down over time."
            ),
            "what_it_means": (
                "This is very common, especially as we get older. It can cause "
                "pain, stiffness, and swelling in your knee. It does not mean "
                "you need surgery — many people manage it very well with the "
                "right care."
            ),
            "what_to_do": (
                "Book an appointment with your doctor or an orthopaedic "
                "specialist. They can suggest exercises, pain relief, or other "
                "treatments to keep you comfortable and mobile."
            ),
            "urgency": "soon",
            "emoji": "🦵",
        },
        "Fracture": {
            "headline": "Possible bone fracture detected",
            "what_found": (
                "The AI found what looks like a break or crack in one of the "
                "bones around your knee."
            ),
            "what_it_means": (
                "A fracture means a bone is broken or cracked. This needs "
                "proper treatment to heal correctly."
            ),
            "what_to_do": (
                "Please go to a hospital or emergency room today. Do not put "
                "weight on the knee until a doctor has examined it."
            ),
            "urgency": "urgent",
            "emoji": "🚨",
        },
        "Ligament Damage": {
            "headline": "Possible ligament injury detected",
            "what_found": (
                "The AI found signs that a ligament — one of the tough bands "
                "that hold your knee together — may be injured."
            ),
            "what_it_means": (
                "Ligament injuries can range from a mild sprain to a complete "
                "tear. They are common in sports injuries and falls."
            ),
            "what_to_do": (
                "See a doctor or sports medicine specialist soon. In the "
                "meantime, rest the knee, apply ice, and avoid strenuous "
                "activity."
            ),
            "urgency": "soon",
            "emoji": "⚠️",
        },
    },
    # ── HAND / WRIST ──────────────────────────────────────────────────────────
    "hand": {
        "Normal": {**_NORMAL_TEMPLATE, "headline": "Your hand looks healthy"},
        "Fracture": {
            "headline": "Possible bone fracture in your hand",
            "what_found": (
                "The AI found what looks like a break or crack in one of the "
                "small bones in your hand or wrist."
            ),
            "what_it_means": (
                "Hand fractures need proper care to heal correctly and avoid "
                "long-term stiffness or weakness."
            ),
            "what_to_do": (
                "Go to a hospital or urgent care today. Your doctor may need "
                "to put your hand in a splint or cast."
            ),
            "urgency": "urgent",
            "emoji": "🚨",
        },
        "Arthritis": {
            "headline": "Signs of arthritis in your hand",
            "what_found": (
                "The AI spotted signs of arthritis — a condition where the "
                "joints in your hand are inflamed or worn down."
            ),
            "what_it_means": (
                "Arthritis in the hand can cause pain, stiffness, and swelling "
                "in your fingers and joints. It is very manageable with the "
                "right treatment."
            ),
            "what_to_do": (
                "See your doctor. There are many treatments including exercises, "
                "medications, and splints that can ease the pain and keep your "
                "hand moving well."
            ),
            "urgency": "soon",
            "emoji": "✋",
        },
    },
    # ── SPINE / BACK ──────────────────────────────────────────────────────────
    "spine": {
        "Normal": {**_NORMAL_TEMPLATE, "headline": "Your spine looks healthy"},
        "Scoliosis": {
            "headline": "Possible spine curve detected",
            "what_found": (
                "The AI found signs of scoliosis — a sideways curve in your "
                "spine instead of it going straight up and down."
            ),
            "what_it_means": (
                "Many people live perfectly normal lives with scoliosis. "
                "Some cases are mild and just need monitoring; others may "
                "benefit from a brace or physical therapy."
            ),
            "what_to_do": (
                "See a doctor or spine specialist. They will measure the "
                "degree of curve and recommend the best plan for you."
            ),
            "urgency": "soon",
            "emoji": "🦴",
        },
        "Disc Degeneration": {
            "headline": "Signs of disc wear detected in your back",
            "what_found": (
                "The AI found signs that the discs between your back bones "
                "(which act like cushions) have worn down."
            ),
            "what_it_means": (
                "This is very common with age and can cause back pain or "
                "stiffness. It is not dangerous but can be uncomfortable."
            ),
            "what_to_do": (
                "See your doctor. Physiotherapy, exercises, and sometimes "
                "medication can make a big difference in managing the pain."
            ),
            "urgency": "soon",
            "emoji": "⚠️",
        },
        "Compression Fracture": {
            "headline": "Possible spine fracture detected",
            "what_found": (
                "The AI found what looks like a fracture in one of your "
                "vertebrae — the bones that make up your spine."
            ),
            "what_it_means": (
                "A compression fracture needs prompt medical attention to "
                "prevent further injury."
            ),
            "what_to_do": (
                "Go to a hospital or emergency room today. Avoid heavy lifting "
                "or strenuous activity until you are evaluated."
            ),
            "urgency": "urgent",
            "emoji": "🚨",
        },
    },
    # ── SHOULDER ──────────────────────────────────────────────────────────────
    "shoulder": {
        "Normal": {**_NORMAL_TEMPLATE, "headline": "Your shoulder looks healthy"},
        "Fracture": {
            "headline": "Possible shoulder fracture detected",
            "what_found": "The AI found signs of a break in one of your shoulder bones.",
            "what_it_means": "Shoulder fractures need treatment to heal correctly.",
            "what_to_do": "Go to a hospital or emergency room today.",
            "urgency": "urgent",
            "emoji": "🚨",
        },
        "Dislocation": {
            "headline": "Possible shoulder dislocation detected",
            "what_found": (
                "The AI found signs that the ball of your shoulder joint "
                "may have slipped out of its socket."
            ),
            "what_it_means": (
                "A dislocation is painful and needs to be put back in place "
                "by a medical professional."
            ),
            "what_to_do": (
                "Go to a hospital or emergency room immediately. Do not try "
                "to put it back yourself."
            ),
            "urgency": "urgent",
            "emoji": "🚨",
        },
        "Rotator Cuff Tear": {
            "headline": "Possible shoulder muscle tear detected",
            "what_found": (
                "The AI found signs of a tear in the rotator cuff — the group "
                "of muscles and tendons that keep your shoulder working."
            ),
            "what_it_means": ("This can cause pain, weakness, and difficulty lifting your arm."),
            "what_to_do": (
                "See a doctor or orthopaedic specialist soon. Many rotator "
                "cuff tears can be treated without surgery."
            ),
            "urgency": "soon",
            "emoji": "⚠️",
        },
    },
    # ── HIP / PELVIS ──────────────────────────────────────────────────────────
    "hip": {
        "Normal": {**_NORMAL_TEMPLATE, "headline": "Your hip looks healthy"},
        "Fracture": {
            "headline": "Possible hip fracture detected",
            "what_found": "The AI found signs of a break in your hip bone.",
            "what_it_means": ("A hip fracture is serious and needs immediate medical attention."),
            "what_to_do": "Go to a hospital emergency room right away.",
            "urgency": "urgent",
            "emoji": "🚨",
        },
        "Osteoarthritis": {
            "headline": "Signs of hip wear and tear detected",
            "what_found": (
                "The AI found signs that the cartilage in your hip joint " "has worn down."
            ),
            "what_it_means": (
                "Hip osteoarthritis is common and causes pain and stiffness. "
                "Many people manage it well with exercise and medication."
            ),
            "what_to_do": (
                "See your doctor. They can recommend exercises, pain relief, "
                "or other treatments."
            ),
            "urgency": "soon",
            "emoji": "⚠️",
        },
    },
    # ── FOOT / ANKLE ──────────────────────────────────────────────────────────
    "foot": {
        "Normal": {**_NORMAL_TEMPLATE, "headline": "Your foot looks healthy"},
        "Fracture": {
            "headline": "Possible bone fracture in your foot",
            "what_found": "The AI found what looks like a break in a bone in your foot or ankle.",
            "what_it_means": "Foot fractures need proper care to heal correctly.",
            "what_to_do": (
                "Go to a hospital or urgent care. Do not put weight on the "
                "foot until a doctor evaluates it."
            ),
            "urgency": "urgent",
            "emoji": "🚨",
        },
        "Flat Foot": {
            "headline": "Flat foot pattern detected",
            "what_found": "The AI found signs of flat feet — where the arch of your foot is lower than usual.",
            "what_it_means": (
                "Flat feet are very common and often cause no problems. "
                "In some cases they can lead to foot pain or fatigue."
            ),
            "what_to_do": (
                "If you have pain, see your doctor. Special shoe inserts "
                "(orthotics) often help a lot."
            ),
            "urgency": "watch",
            "emoji": "🦶",
        },
    },
    # ── SKULL / HEAD ──────────────────────────────────────────────────────────
    "skull": {
        "Normal": {**_NORMAL_TEMPLATE, "headline": "Your skull looks healthy"},
        "Fracture": {
            "headline": "Possible skull fracture detected",
            "what_found": "The AI found signs of a break in your skull.",
            "what_it_means": (
                "A skull fracture is serious and requires immediate medical attention."
            ),
            "what_to_do": "Go to a hospital emergency room immediately.",
            "urgency": "urgent",
            "emoji": "🚨",
        },
    },
    # ── ABDOMEN ───────────────────────────────────────────────────────────────
    "abdomen": {
        "Normal": {**_NORMAL_TEMPLATE, "headline": "Your abdomen looks healthy"},
        "Bowel Obstruction": {
            "headline": "Possible blockage in your digestive system",
            "what_found": ("The AI found signs that something may be blocking your " "intestines."),
            "what_it_means": (
                "A bowel obstruction stops food and liquid from passing through "
                "normally and can become serious if not treated."
            ),
            "what_to_do": "Go to a hospital emergency room right away.",
            "urgency": "urgent",
            "emoji": "🚨",
        },
    },
    # ── FOREARM / ELBOW / LEG — generic fracture/normal ──────────────────────
    "forearm": {
        "Normal": {**_NORMAL_TEMPLATE, "headline": "Your forearm looks healthy"},
        "Fracture": {
            "headline": "Possible bone fracture in your forearm",
            "what_found": "The AI found signs of a break in one of the bones in your forearm.",
            "what_it_means": "Forearm fractures need treatment to heal straight.",
            "what_to_do": "Go to a hospital or urgent care today.",
            "urgency": "urgent",
            "emoji": "🚨",
        },
    },
    "elbow": {
        "Normal": {**_NORMAL_TEMPLATE, "headline": "Your elbow looks healthy"},
        "Fracture": {
            "headline": "Possible elbow fracture detected",
            "what_found": "The AI found signs of a break near your elbow joint.",
            "what_it_means": "Elbow fractures need proper treatment to regain full movement.",
            "what_to_do": "Go to a hospital or urgent care today.",
            "urgency": "urgent",
            "emoji": "🚨",
        },
    },
    "leg": {
        "Normal": {**_NORMAL_TEMPLATE, "headline": "Your leg looks healthy"},
        "Fracture": {
            "headline": "Possible leg fracture detected",
            "what_found": "The AI found signs of a break in a bone in your lower leg.",
            "what_it_means": "Leg fractures need proper medical care to heal correctly.",
            "what_to_do": (
                "Go to a hospital. Do not put weight on the leg until " "a doctor has seen you."
            ),
            "urgency": "urgent",
            "emoji": "🚨",
        },
    },
}


def get_patient_summary(body_part: str, prediction: str, confidence: float) -> dict:
    """
    Returns a plain-English patient summary for a given AI result.

    Args:
        body_part:  e.g. "chest", "knee"
        prediction: e.g. "Pneumonia", "Normal"
        confidence: float 0-1

    Returns dict with: headline, what_found, what_it_means, what_to_do, urgency, emoji,
                        confidence_text, body_part
    """
    part_templates = PATIENT_LANGUAGE.get(body_part, {})

    # Find matching condition (case-insensitive, partial match)
    template = None
    for cond, tmpl in part_templates.items():
        if cond.lower() == prediction.lower():
            template = tmpl
            break

    # If not found, use Normal fallback
    if template is None:
        if prediction.lower() == "normal":
            template = {**_NORMAL_TEMPLATE}
        else:
            # Unknown condition — generic warning
            template = {
                "headline": f"Something was detected in your {body_part.replace('_', ' ')}",
                "what_found": (
                    f"The AI detected {prediction} in your " f"{body_part.replace('_', ' ')} X-ray."
                ),
                "what_it_means": (
                    "Please discuss this result with your doctor for a " "full explanation."
                ),
                "what_to_do": "Book an appointment with your doctor soon.",
                "urgency": "soon",
                "emoji": "⚠️",
            }

    # Fill in {part} placeholders
    part_label = body_part.replace("_", " ")
    result = {
        k: (v.format(part=part_label) if isinstance(v, str) else v) for k, v in template.items()
    }

    # Confidence in plain English
    pct = round(confidence * 100)
    if pct >= 90:
        conf_text = f"The AI is very confident in this result ({pct}%)."
    elif pct >= 75:
        conf_text = (
            f"The AI is fairly confident in this result ({pct}%). Your doctor should confirm."
        )
    else:
        conf_text = f"The AI is less certain about this result ({pct}%). A doctor's review is especially important."

    result["confidence_text"] = conf_text
    result["body_part_label"] = part_label.title()
    result["prediction"] = prediction

    return result
