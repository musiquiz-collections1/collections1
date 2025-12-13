import datetime
import hashlib

# Expanded word banks
word_banks = [
    # Position 1
    ["Alpha", "Brave", "Cosmic", "Digital", "Electric", "Frozen", "Golden", 
     "Hidden", "Iron", "Jade", "Mystic", "Noble", "Omega", "Prime", "Quantum",
     "Royal", "Solar", "Titan", "Ultra", "Void", "Wild", "Xeno", "Zenith"],
    
    # Position 2  
    ["Lion", "Dragon", "Eagle", "Phoenix", "Tiger", "Wolf", "Hawk", 
     "Falcon", "Raven", "Owl", "Shark", "Bear", "Fox", "Panther", "Griffin",
     "Basilisk", "Chimera", "Hydra", "Kraken", "Manticore", "Pegasus", "Unicorn"],
    
    # Position 3
    ["Stone", "Fire", "Storm", "Blade", "Shield", "Star", "Moon", 
     "Sun", "Wave", "Flame", "Ice", "Light", "Shadow", "Metal", "Crystal",
     "Earth", "Air", "Water", "Energy", "Plasma", "Vortex", "Nova"],
    
    # Position 4
    ["Bolt", "X", "Mark", "Core", "Edge", "Shift", "Pulse", "Spark", 
     "Surge", "Flux", "Beam", "Ray", "Field", "Ring", "Disk",
     "Node", "Gate", "Key", "Lock", "Chain", "Grid", "Web"],
    
    # Position 5
    ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta", 
     "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi", "Omicron",
     "Pi", "Rho", "Sigma", "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega"]
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
    
    return "<br>".join(parts)

# Generate all words
all_words = []
unique_check = set()

for minute in range(1440):
    word = minute_to_scrambled_word(minute)
    all_words.append(word)
    unique_check.add(word)

def get_word(hour, minute):
    return all_words[hour * 60 + minute]

