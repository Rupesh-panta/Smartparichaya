import random
from sympy import isprime, mod_inverse

def match_job_template(job_title, job_skills):
    """
    Enhanced Algorithm: Prioritized Rule-Based Template Matching
    """
    title = job_title.lower()
    skills = [s.lower().strip() for s in job_skills]

    # 1. High Priority: Creative / Design (Focus on UI/UX specifically)
    creative_indicators = ['designer', 'marketing', 'content', 'ui', 'ux', 'video', 'creative', 'graphics', 'branding']
    if any(word in title for word in creative_indicators) or any(s in creative_indicators for s in skills):
        return "creative"

    # 2. Medium Priority: Technical / Engineering
    tech_indicators = ['software', 'developer', 'engineer', 'python', 'java', 'it', 'web', 'backend', 'frontend', 'data science', 'sql']
    if any(word in title for word in tech_indicators) or any(s in tech_indicators for s in skills):
        return "technical"

    # 3. Low Priority: Management / Business
    prof_indicators = ['manager', 'hr', 'finance', 'accountant', 'sales', 'lead', 'director', 'operations', 'executive']
    if any(word in title for word in prof_indicators) or any(s in prof_indicators for s in skills):
        return "professional"

    # Default fallback
    return "simple"
# Generate two distinct prime numbers
def generate_prime_candidate(length):
    p = random.getrandbits(length)
    return p | (1 << length - 1) | 1  # Ensure p is odd and of the desired bit length


def generate_prime_number(length=128):  # Use larger prime numbers
    p = 4
    while not isprime(p):
        p = generate_prime_candidate(length)
    return p


def generate_rsa_keys():
    p = generate_prime_number(128)  # Larger prime number for stronger encryption
    q = generate_prime_number(128)
    n = p * q
    phi = (p - 1) * (q - 1)
    e = 65537  # Commonly used prime for public key exponent
    d = mod_inverse(e, phi)
    return (e, n), (d, n)  # Public key, Private key


def rsa_encrypt(plaintext, public_key):
    e, n = public_key
    plaintext = plaintext.zfill(
        6
    )  # Ensure 6 digits are maintained, including leading zeros
    plaintext_int = int.from_bytes(
        plaintext.encode(), "big"
    )  # Convert plaintext to int
    ciphertext = pow(plaintext_int, e, n)
    return ciphertext


def rsa_decrypt(ciphertext, private_key):
    d, n = private_key
    decrypted_int = pow(ciphertext, d, n)
    decrypted_bytes = decrypted_int.to_bytes(
        (decrypted_int.bit_length() + 7) // 8, "big"
    )
    return decrypted_bytes.decode().lstrip("0")  # Decode bytes and strip leading zeros
