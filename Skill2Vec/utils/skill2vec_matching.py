import numpy as np
from numpy.linalg import norm

def get_skill_vector(skill, model):
    """
    Retrieves the vector for a given skill from the Word2Vec model.
    
    Args:
    - skill (str): The name of the skill.
    - model (Word2Vec): The trained Word2Vec model.
    
    Returns:
    - np.ndarray: The vector representing the skill, or None if the skill is not in the model.
    """
    if skill in model.wv:
        return model.wv[skill]
    return None

def get_skillset_vector(skills, model):
    """
    Calculates the average vector for a set of skills by averaging the individual skill vectors.
    
    Args:
    - skills (list): A list of skill names.
    - model (Word2Vec): The trained Word2Vec model.
    
    Returns:
    - np.ndarray: The average vector representing the skillset, or a zero vector if no valid vectors are found.
    """
    vectors = [get_skill_vector(skill, model) for skill in skills if get_skill_vector(skill, model) is not None]
    if not vectors:
        return np.zeros(model.vector_size)
    return np.mean(vectors, axis=0)

def cosine_similarity(vec1, vec2):
    """
    Computes the cosine similarity between two vectors.
    
    Args:
    - vec1 (np.ndarray): The first vector.
    - vec2 (np.ndarray): The second vector.
    
    Returns:
    - float: The cosine similarity between the two vectors.
    """
    if norm(vec1) == 0 or norm(vec2) == 0:
        return 0.0
    return np.dot(vec1, vec2) / (norm(vec1) * norm(vec2))

def skillset_similarity(skills1, skills2, model):
    """
    Calculates the similarity between two skill sets using their vector representations.
    
    Args:
    - skills1 (list): A list of skills for the first skillset.
    - skills2 (list): A list of skills for the second skillset.
    - model (Word2Vec): The trained Word2Vec model.
    
    Returns:
    - float: The cosine similarity between the two skill sets.
    """
    vec1 = get_skillset_vector(skills1, model)
    vec2 = get_skillset_vector(skills2, model)
    return cosine_similarity(vec1, vec2)
