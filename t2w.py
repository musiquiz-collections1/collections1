import datetime
import hashlib

# Expanded word banks
word_banks = [
    ["Badger", "Bear", "Beaver", "Condor", "Coyote",
     "Eagle", "Falcon", "Gorilla", "Hippo", "Jaguar",
     "Lion", "Mantis", "Orca", "Otter", "Python",
     "Rhino", "Shark", "Tiger", "Walrus", "Weasel",
     "Wolf", "Zebra"],

    ["Andromeda", "Auriga", "Corvus", "Cygnus", "Delphinus",
     "Dorado", "Draco", "Gemini", "Lacerta", "Cetus",
     "Libra", "Lynx", "Lyra", "Ophiuchus", "Orion",
     "Pegasus", "Perseus", "Pisces", "Sagittarius", "Indus",
     "Taurus", "Vulpecula"],

    ["Calcination", "Carbonization", "Combustion", "Condensation", "Decomposition",
     "Displacement", "Distillation", "Electrolysis", "Fermentation", "Halogenation",
     "Hydration", "Hydrolysis", "Isomerization", "Neutralization", "Nitration",
     "Oxidation", "Polymerization", "Precipitation", "Pyrolysis", "Reduction",
     "Sublimation", "Synthesis"],

    ["Argon", "Barium", "Calcium", "Carbon", "Cerium",
     "Cobalt", "Copper", "Germanium", "Helium", "Iodine",
     "Molybdenum", "Neptunium", "Nickel", "Osmium", "Plutonium",
     "Potassium", "Radon", "Silicon", "Sodium", "Tellurium",
     "Titanium", "Uranium"],

    ["Agate", "Amber", "Amethyst", "Beryl", "Citrine",
     "Diamond", "Emerald", "Garnet", "Jade", "Jasper",
     "Lapis", "Malachite", "Obsidian", "Onyx", "Opal",
     "Peridot", "Quartz", "Ruby", "Sapphire", "Spinel",
     "Topaz", "Zircon"]
]
def create_permuted_mapping():
    """Create a completely permuted mapping for maximum randomness"""
    # Use different hash seeds for each position
    mapping = []
    
    for pos in range(5):
        # Create permutation for this position
        perm = list(range(len(word_banks[pos])))
        
        # Shuffle deterministically based on position seed
        seed = f"position_{pos}_seed".encode()
        hash_val = hashlib.md5(seed).digest()
        
        # Simple deterministic shuffle
        for i in range(len(perm)-1, 0, -1):
            # Use hash bytes to pick swap index
            byte_idx = i % len(hash_val)
            j = hash_val[byte_idx] % (i + 1)
            perm[i], perm[j] = perm[j], perm[i]
        
        mapping.append(perm)
    
    return mapping

# Create the mapping once
permuted_mapping = create_permuted_mapping()

def minute_to_scrambled_word(minute):
    """Convert minute to completely scrambled word"""
    parts = []
    
    # Scramble minute differently for each position
    for pos in range(5):
        # Different transformation for each position
        if pos == 0:
            val = (minute * 0x6D2B79F5) & 0xFFFFFFFF  # Multiply by large prime
        elif pos == 1:
            val = ((minute << 13) | (minute >> 19)) & 0xFFFFFFFF  # Rotate
        elif pos == 2:
            val = minute ^ 0xDEADBEEF  # XOR with constant
        elif pos == 3:
            val = ((minute * 0x19660D) + 0x3C6EF35F) & 0xFFFFFFFF  # LCG
        else:  # pos == 4
            val = ((minute & 0x55555555) << 1) | ((minute & 0xAAAAAAAA) >> 1)  # Swap bits
        
        # Map to word using permuted index
        word_list = word_banks[pos]
        perm = permuted_mapping[pos]
        idx = val % len(word_list)
        parts.append(word_list[perm[idx]])
    
    return "".join(parts)

# Generate all words
all_words = []
unique_check = set()

for minute in range(1440):
    word = minute_to_scrambled_word(minute)
    all_words.append(word)
    unique_check.add(word)

def get_word(hour, minute):
    return all_words[hour * 60 + minute]

