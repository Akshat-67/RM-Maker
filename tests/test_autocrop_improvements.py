import pytest
import numpy as np
import cv2
from services.autocrop import DocumentConfig, DocumentCandidate

def test_document_config_and_candidate_types():
    cfg = DocumentConfig(target_aspect_ratio=1.585)
    assert cfg.target_aspect_ratio == 1.585
    assert cfg.min_solidity == 0.70

    cand = DocumentCandidate(
        contour=np.array([[0,0], [10,0], [10,10], [0,10]]),
        bounding_box=(0, 0, 10, 10),
        approx_polygon=np.array([[0,0], [10,0], [10,10], [0,10]]),
        is_quadrilateral=True,
        aspect_ratio=1.0,
        solidity=1.0,
        convexity=1.0,
        rectangularity=1.0,
        edge_support=0.9,
        hierarchy_status="independent"
    )
    assert cand.is_quadrilateral is True
    assert cand.score == 0.0
    assert cand.is_valid is True

def test_preprocess_image():
    from services.autocrop import preprocess_image
    # Make a dummy BGR image (200x200x3)
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.rectangle(img, (20, 20), (180, 180), (255, 255, 255), -1)
    
    gray, edges = preprocess_image(img)
    assert gray.shape == (200, 200)
    assert edges.shape == (200, 200)

def test_find_candidate_contours():
    from services.autocrop import preprocess_image, find_candidate_contours
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    # Draw a rectangle to act as a document
    cv2.rectangle(img, (50, 50), (250, 200), (255, 255, 255), -1)
    
    gray, edges = preprocess_image(img)
    candidates = find_candidate_contours(img, edges)
    
    assert len(candidates) > 0
    found_close = False
    for cand in candidates:
        x, y, w, h = cand.bounding_box
        # Allow minor expansion due to edge dilation
        if abs(x - 50) < 30 and abs(y - 50) < 30 and abs(w - 200) < 60 and abs(h - 150) < 60:
            found_close = True
            break
    assert found_close, f"No candidate close to expected box was found. Candidates: {[c.bounding_box for c in candidates]}"

