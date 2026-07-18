import pytest
import numpy as np
import cv2
from services.autocrop import DocumentConfig, DocumentCandidate

def test_document_config_and_candidate_types():
    cfg = DocumentConfig(target_aspect_ratios=[1.585])
    assert cfg.target_aspect_ratios == [1.585]
    assert cfg.min_solidity == 0.65

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

def test_score_candidates():
    from services.autocrop import score_candidates, DocumentConfig, DocumentCandidate
    
    cfg = DocumentConfig(target_aspect_ratios=[1.585])
    edges = np.zeros((100, 100), dtype=np.uint8)
    
    # Candidate A: close to Aadhaar card
    cand_a = DocumentCandidate(
        contour=np.array([[0,0], [15,0], [15,10], [0,10]]),
        bounding_box=(0, 0, 15, 10),
        approx_polygon=np.array([[0,0], [15,0], [15,10], [0,10]]),
        is_quadrilateral=True,
        aspect_ratio=1.5,
        solidity=0.95,
        convexity=0.95,
        rectangularity=0.95,
        edge_support=0.8,
        hierarchy_status="parent"
    )
    
    # Candidate B: extreme aspect ratio
    cand_b = DocumentCandidate(
        contour=np.array([[0,0], [50,0], [50,5], [0,5]]),
        bounding_box=(0, 0, 50, 5),
        approx_polygon=np.array([[0,0], [50,0], [50,5], [0,5]]),
        is_quadrilateral=True,
        aspect_ratio=10.0,
        solidity=0.95,
        convexity=0.95,
        rectangularity=0.95,
        edge_support=0.8,
        hierarchy_status="child"
    )
    
    scored = score_candidates([cand_b, cand_a], cfg, edges)
    # Cand A should have higher score and come first
    assert scored[0] == cand_a
    assert cand_a.score > cand_b.score

def test_warp_candidate():
    from services.autocrop import warp_candidate, DocumentCandidate
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    # Skewed quad corners (roughly a rotated card)
    pts = np.array([[[50, 60]], [[250, 40]], [[260, 200]], [[40, 220]]], dtype=np.int32)
    
    cand = DocumentCandidate(
        contour=pts,
        bounding_box=(40, 40, 220, 180),
        approx_polygon=pts,
        is_quadrilateral=True,
        aspect_ratio=1.3,
        solidity=0.9,
        convexity=0.9,
        rectangularity=0.9,
        edge_support=0.9,
        hierarchy_status="independent"
    )
    
    warped = warp_candidate(img, cand)
    # Warped image should be a horizontal rectangle
    assert warped is not None
    assert warped.shape[1] > 100
    assert warped.shape[0] > 100

def test_refine_crop():
    from services.autocrop import refine_crop
    img = np.zeros((200, 300, 3), dtype=np.uint8)
    # Draw a card inside, leaving black margins on the edges (5 pixels margin)
    cv2.rectangle(img, (5, 5), (295, 195), (255, 255, 255), -1)
    
    refined = refine_crop(img)
    # Refined image should crop out the black margin, making it smaller than 300x200
    assert refined.shape[1] < 300
    assert refined.shape[0] < 200

def test_grabcut_with_expansion():
    from services.autocrop import _grabcut_with_expansion, DocumentCandidate
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    # Draw a card inside
    cv2.rectangle(img, (40, 40), (260, 260), (255, 255, 255), -1)
    
    # We pass a DocumentCandidate to initialize GrabCut
    cand = DocumentCandidate(
        contour=np.array([[[40, 40]], [[260, 40]], [[260, 260]], [[40, 260]]], dtype=np.int32),
        bounding_box=(40, 40, 220, 220),
        approx_polygon=np.array([[[40, 40]], [[260, 40]], [[260, 260]], [[40, 260]]], dtype=np.int32),
        is_quadrilateral=True,
        aspect_ratio=1.0,
        solidity=0.9,
        convexity=0.9,
        rectangularity=0.9,
        edge_support=0.9,
        hierarchy_status="independent"
    )
    
    box = _grabcut_with_expansion(img, cand)
    assert box is not None
    assert box[2] - box[0] > 100

def test_debug_mode_and_reporting(tmp_path):
    from services.autocrop import save_candidate_scores_png, log_candidate_report, DocumentConfig, DocumentCandidate
    import os
    
    cfg = DocumentConfig()
    cand = DocumentCandidate(
        contour=np.array([[0,0], [15,0], [15,10], [0,10]]),
        bounding_box=(0, 0, 15, 10),
        approx_polygon=np.array([[0,0], [15,0], [15,10], [0,10]]),
        is_quadrilateral=True,
        aspect_ratio=1.5,
        solidity=0.9,
        convexity=0.9,
        rectangularity=0.9,
        edge_support=0.8,
        hierarchy_status="independent",
        score=0.85,
        is_valid=True
    )
    
    # 1. Test log report
    log_candidate_report([cand], cfg)
    
    # 2. Test scores PNG rendering
    png_path = os.path.join(tmp_path, "08_candidate_scores.png")
    save_candidate_scores_png([cand], png_path)
    assert os.path.exists(png_path)
    assert os.path.getsize(png_path) > 0

def test_crop_via_opencv_integration(tmp_path):
    from services.autocrop import crop_via_opencv
    import os
    img_path = os.path.join(tmp_path, "card.jpg")
    img = np.zeros((400, 400, 3), dtype=np.uint8)
    # Draw a clean card with high aspect ratio (~1.58)
    cv2.rectangle(img, (50, 100), (290, 250), (255, 255, 255), -1)
    # Draw some detail lines to simulate text / edges
    cv2.line(img, (70, 140), (200, 140), (0, 0, 0), 2)
    cv2.line(img, (70, 180), (150, 180), (0, 0, 0), 2)
    cv2.imwrite(img_path, img)
    
    box = crop_via_opencv(img_path)
    assert box is not None
    # If perspective warped, it returns (0, 0, 0, 0)
    assert box == (0, 0, 0, 0) or (box[2] - box[0] > 100)






