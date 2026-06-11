import numpy as np
from phe import paillier
import tenseal as ts

# =====================================================
#  PARTIAL HOMOMORPHIC ENCRYPTION (Paillier)
# =====================================================
public_key, private_key = paillier.generate_paillier_keypair()


# =====================================================
#  FULL HOMOMORPHIC ENCRYPTION (CKKS - TenSEAL)
# =====================================================
ckks_context = ts.context(
    ts.SCHEME_TYPE.CKKS,
    poly_modulus_degree=8192,
    coeff_mod_bit_sizes=[60, 40, 40, 60]
)

ckks_context.global_scale = 2**40
ckks_context.generate_galois_keys()


# =====================================================
#  ENCRYPT EMBEDDING USING PHE
# =====================================================
def encrypt_phe(embedding):
    """
    Encrypt first 32 values using Paillier (Fast Filter)
    """
    return [public_key.encrypt(float(x)) for x in embedding[:32]]


# =====================================================
#  ENCRYPT EMBEDDING USING FHE
# =====================================================
# =====================================================
# Fixed Embedding Size (IMPORTANT)
# =====================================================
EMB_SIZE = 128


# =====================================================
# Encrypt Embedding Using FHE
# =====================================================
def encrypt_fhe(embedding):
    """
    Encrypt first 128 values using CKKS (Secure Matching)
    """
    vec = ts.ckks_vector(ckks_context, embedding[:EMB_SIZE].tolist())
    return vec.serialize()


# =====================================================
#  PHE DISTANCE (Fast Filter)
# =====================================================
def phe_distance(enc1, enc2):
    """
    Decrypt small part and compute Euclidean distance.
    Used only for filtering.
    """
    v1 = np.array([private_key.decrypt(x) for x in enc1])
    v2 = np.array([private_key.decrypt(x) for x in enc2])

    return np.linalg.norm(v1 - v2)


# =====================================================
#  FHE SIMILARITY SCORE (Dot Product)
# =====================================================
def fhe_similarity(enc_vec1, enc_vec2):
    """
    Compute encrypted dot product similarity score
    """
    v1 = ts.ckks_vector_from(ckks_context, enc_vec1)
    v2 = ts.ckks_vector_from(ckks_context, enc_vec2)

    score = v1.dot(v2)

    return score.serialize()


# =====================================================
#  DECRYPT FINAL SCORE ONLY
# =====================================================
def decrypt_score(enc_score):
    """
    Decrypt only similarity score (not embedding)
    """
    vec = ts.ckks_vector_from(ckks_context, enc_score)
    return vec.decrypt()[0]
