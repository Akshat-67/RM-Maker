import os
import json
import logging
import shutil
from dataclasses import dataclass
from typing import Optional, List, Tuple
import cv2
import numpy as np
from PIL import Image
from services.ai_client import AIClient
from utils.config import DEFAULT_GEMINI_API_KEYS

logger = logging.getLogger("Autocrop")


@dataclass
class DocumentConfig:
    target_aspect_ratio: float = 1.585
    aspect_ratio_tolerance: float = 0.3
    min_area_ratio: float = 0.15
    max_area_ratio: float = 0.95
    min_solidity: float = 0.70
    min_convexity: float = 0.70
    min_rectangularity: float = 0.70
    edge_support_threshold: float = 0.30


@dataclass
class DocumentCandidate:
    contour: np.ndarray
    bounding_box: Tuple[int, int, int, int]  # (x, y, w, h)
    approx_polygon: np.ndarray
    is_quadrilateral: bool
    aspect_ratio: float
    solidity: float
    convexity: float
    rectangularity: float
    edge_support: float
    hierarchy_status: str  # "parent", "child", "independent"
    score: float = 0.0
    is_valid: bool = True
    rejection_reason: str = ""



def preprocess_image(img: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    BGR -> Gray -> Gaussian Blur -> Canny Edges
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    v_median = np.median(blurred)
    lower = int(max(0, 0.5 * v_median))
    upper = int(min(255, 1.5 * v_median))
    edges = cv2.Canny(blurred, lower, upper)
    return blurred, edges


def find_candidate_contours(img: np.ndarray, edges: np.ndarray) -> List[DocumentCandidate]:
    """
    Extracts contours, processes geometric features, builds tree hierarchy,
    and returns a list of DocumentCandidate instances.
    """
    h_img, w_img = img.shape[:2]
    img_area = h_img * w_img
    candidates = []

    for dilation_iter in [3, 5, 8]:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        dilated = cv2.dilate(edges, kernel, iterations=dilation_iter)
        dilated = cv2.morphologyEx(
            dilated, cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15)),
        )

        contours, hierarchy = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if contours is None or len(contours) == 0 or hierarchy is None:
            continue

        hierarchy = hierarchy[0]

        for idx, c in enumerate(contours):
            area = cv2.contourArea(c)
            if area < 0.02 * img_area:
                continue

            x, y, w, h = cv2.boundingRect(c)
            bbox_area = w * h
            solidity = area / bbox_area if bbox_area > 0 else 0
            aspect = max(w, h) / max(min(w, h), 1)

            hull = cv2.convexHull(c)
            hull_area = cv2.contourArea(hull)
            convexity = area / hull_area if hull_area > 0 else 0

            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            is_quad = (len(approx) == 4)

            parent_idx = hierarchy[idx][3]
            child_idx = hierarchy[idx][2]

            status = "independent"
            if parent_idx != -1:
                p_area = cv2.contourArea(contours[parent_idx])
                if p_area > area * 1.1:
                    status = "child"
            elif child_idx != -1:
                status = "parent"

            candidate = DocumentCandidate(
                contour=c,
                bounding_box=(x, y, w, h),
                approx_polygon=approx,
                is_quadrilateral=is_quad,
                aspect_ratio=aspect,
                solidity=solidity,
                convexity=convexity,
                rectangularity=solidity,
                edge_support=0.0,
                hierarchy_status=status
            )
            candidates.append(candidate)

    # De-duplicate identical bounding boxes to prevent redundant checks
    unique_candidates = []
    seen_boxes = set()
    for cand in candidates:
        if cand.bounding_box not in seen_boxes:
            seen_boxes.add(cand.bounding_box)
            unique_candidates.append(cand)

    unique_candidates.sort(key=lambda c: cv2.contourArea(c.contour), reverse=True)
    return unique_candidates


def score_candidates(
    candidates: List[DocumentCandidate],
    cfg: DocumentConfig,
    edges: np.ndarray
) -> List[DocumentCandidate]:
    """
    Computes a normalized weighted confidence score for each document candidate.
    Filters and sorts the candidates by score descending.
    """
    dilated_edges = cv2.dilate(edges, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
    h_img, w_img = edges.shape[:2]

    for cand in candidates:
        pts = cand.contour.reshape(-1, 2)
        if len(pts) > 0:
            xs = np.clip(pts[:, 0], 0, w_img - 1)
            ys = np.clip(pts[:, 1], 0, h_img - 1)
            edge_pixels = dilated_edges[ys, xs]
            cand.edge_support = float(np.sum(edge_pixels > 0) / len(pts))
        else:
            cand.edge_support = 0.0

        # 1. Aspect Ratio similarity score
        aspect_diff = abs(cand.aspect_ratio - cfg.target_aspect_ratio)
        s_aspect = float(np.exp(-aspect_diff / cfg.aspect_ratio_tolerance))

        # 2. Solidity score
        s_solidity = float(cand.solidity)

        # 3. Convexity score
        s_convexity = float(cand.convexity)

        # 4. Rectangularity score
        s_rect = float(cand.rectangularity)

        # 5. Vertex count score (prefers quadrilaterals)
        if cand.is_quadrilateral:
            s_vertex = 1.0
        elif len(cand.approx_polygon) <= 6:
            s_vertex = 0.6
        else:
            s_vertex = 0.2

        # 6. Edge support score
        s_edge = float(cand.edge_support)

        # 7. Hierarchy score (penalizes child contours inside larger parent cards)
        if cand.hierarchy_status == "child":
            s_hierarchy = 0.2
        else:
            s_hierarchy = 1.0

        # Calculate final weighted sum (weights sum to 1.0)
        cand.score = float(
            0.25 * s_aspect +
            0.15 * s_solidity +
            0.15 * s_rect +
            0.15 * s_vertex +
            0.15 * s_edge +
            0.10 * s_hierarchy +
            0.05 * s_convexity
        )

    # Sort candidates by score descending
    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates


def log_candidate_report(candidates: List[DocumentCandidate], cfg: DocumentConfig):
    """Logs a cleanly formatted ASCII table report showing candidates sorted by score."""
    report_lines = [
        "",
        "=====================================================================",
        "                      CANDIDATE CONTOUR REPORT                       ",
        "=====================================================================",
        f"Target Aspect Ratio: {cfg.target_aspect_ratio} | Total Candidates: {len(candidates)}",
        "---------------------------------------------------------------------",
    ]
    for idx, c in enumerate(candidates):
        x, y, w, h = c.bounding_box
        status_symbol = "✓ ACCEPTED" if c.is_valid else f"✗ REJECTED: {c.rejection_reason}"
        report_lines.append(
            f"Contour #{idx+1:02d}: Score={c.score:.4f} | {status_symbol}\n"
            f"  - Geometry: Area={cv2.contourArea(c.contour):.0f} | BBox=(x={x}, y={y}, w={w}, h={h}) | Aspect={c.aspect_ratio:.2f}\n"
            f"  - Metrics: Solidity={c.solidity:.2f} | Convexity={c.convexity:.2f} | Rectangularity={c.rectangularity:.2f}\n"
            f"  - Edge Support: {c.edge_support:.4f} | Hierarchy: {c.hierarchy_status} | Vertices={len(c.approx_polygon)}"
        )
    report_lines.append("=====================================================================")
    logger.info("\n".join(report_lines))


def save_candidate_scores_png(candidates: List[DocumentCandidate], path: str):
    """Renders a text table of candidate scores onto a black canvas and saves it as PNG."""
    canvas_h = 40 + len(candidates) * 50
    canvas = np.zeros((max(200, canvas_h), 800, 3), dtype=np.uint8)

    cv2.putText(canvas, "RANK  SCORE   ASPECT  SOLIDITY  RECT  EDGES  VERTICES  STATUS", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    for idx, c in enumerate(candidates):
        y_offset = 65 + idx * 50
        status = "VALID" if c.is_valid else "INVALID"
        status_color = (0, 255, 0) if c.is_valid else (0, 0, 255)

        info_str = f"#{idx+1:<3d}  {c.score:.3f}   {c.aspect_ratio:.2f}    {c.solidity:.2f}      {c.rectangularity:.2f}  {c.edge_support:.2f}   {len(c.approx_polygon):<8d}"

        cv2.putText(canvas, info_str, (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)
        cv2.putText(canvas, status, (680, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, status_color, 1, cv2.LINE_AA)

        if not c.is_valid:
            cv2.putText(canvas, f"  Reason: {c.rejection_reason[:75]}", (10, y_offset + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (100, 100, 250), 1, cv2.LINE_AA)

    cv2.imwrite(path, canvas)


def validate_candidates(
    candidates: List[DocumentCandidate],
    cfg: DocumentConfig,
    img: np.ndarray,
    edges: np.ndarray
) -> List[DocumentCandidate]:
    """Validates each DocumentCandidate against standard geometric card guidelines."""
    h_img, w_img = img.shape[:2]
    img_area = h_img * w_img

    for cand in candidates:
        x, y, w, h = cand.bounding_box
        area = cv2.contourArea(cand.contour)

        # 1. Area thresholds
        if area < cfg.min_area_ratio * img_area:
            cand.is_valid = False
            cand.rejection_reason = f"Area too small ({area/img_area:.2f} < {cfg.min_area_ratio})"
            continue
        if area > cfg.max_area_ratio * img_area:
            cand.is_valid = False
            cand.rejection_reason = f"Area too large ({area/img_area:.2f} > {cfg.max_area_ratio})"
            continue

        # 2. Solidity
        if cand.solidity < cfg.min_solidity:
            cand.is_valid = False
            cand.rejection_reason = f"Solidity too low ({cand.solidity:.2f} < {cfg.min_solidity})"
            continue

        # 3. Convexity
        if cand.convexity < cfg.min_convexity:
            cand.is_valid = False
            cand.rejection_reason = f"Convexity too low ({cand.convexity:.2f} < {cfg.min_convexity})"
            continue

        # 4. Rectangularity
        if cand.rectangularity < cfg.min_rectangularity:
            cand.is_valid = False
            cand.rejection_reason = f"Rectangularity too low ({cand.rectangularity:.2f} < {cfg.min_rectangularity})"
            continue

        # 5. Aspect Ratio bounds
        if cand.aspect_ratio < 1.2 or cand.aspect_ratio > 2.5:
            cand.is_valid = False
            cand.rejection_reason = f"Aspect ratio out of bounds ({cand.aspect_ratio:.2f})"
            continue

        # 6. Edge Support
        if cand.edge_support < cfg.edge_support_threshold:
            cand.is_valid = False
            cand.rejection_reason = f"Edge support too low ({cand.edge_support:.2f} < {cfg.edge_support_threshold})"
            continue

        # 7. Discarded Edge Density (outer content check)
        x1, y1, x2, y2 = x, y, x + w, y + h
        box_mask = np.zeros_like(edges)
        box_mask[y1:y2, x1:x2] = 255
        inner_edges = np.sum((edges > 0) & (box_mask == 255))
        outer_edges = np.sum(edges > 0) - inner_edges
        outer_area = img_area - (w * h)
        outer_density = outer_edges / outer_area if outer_area > 0 else 0
        if outer_density > 0.012:
            cand.is_valid = False
            cand.rejection_reason = f"Outer density too high ({outer_density:.4f} > 0.012)"
            continue

        # 8. Covers full image check
        w_ratio = w / w_img
        h_ratio = h / h_img
        if w_ratio > 0.92 and h_ratio > 0.88:
            cand.is_valid = False
            cand.rejection_reason = "Covers full image (already cropped)"
            continue

        cand.is_valid = True

    return candidates


def _order_points(pts: np.ndarray) -> np.ndarray:
    pts = pts.reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def warp_candidate(img: np.ndarray, candidate: DocumentCandidate) -> np.ndarray:
    """
    Warps the candidate region using perspective warping if it has 4 corners,
    otherwise crops using axis-aligned bounding box.
    """
    h_img, w_img = img.shape[:2]

    if candidate.is_quadrilateral and len(candidate.approx_polygon) == 4:
        rect = _order_points(candidate.approx_polygon)
        (tl, tr, br, bl) = rect

        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))

        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))

        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]], dtype="float32")

        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(img, M, (maxWidth, maxHeight))
        return warped
    else:
        x, y, w, h = candidate.bounding_box
        x = max(0, x)
        y = max(0, y)
        w = min(w_img - x, w)
        h = min(h_img - y, h)
        return img[y:y+h, x:x+w]


def refine_crop(warped_img: np.ndarray) -> np.ndarray:
    """
    Runs a second-pass contour detection on the warped crop to shave off remaining
    background slivers or padding artifacts at the borders.
    """
    h, w = warped_img.shape[:2]
    gray = cv2.cvtColor(warped_img, cv2.COLOR_BGR2GRAY)

    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    best_box = None
    max_area = 0

    for binary_map in [thresh, cv2.bitwise_not(thresh)]:
        contours, _ = cv2.findContours(binary_map, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            area = cv2.contourArea(c)
            if area > 0.60 * (w * h) and area < 0.98 * (w * h):
                x, y, cw, ch = cv2.boundingRect(c)
                if cw >= 0.99 * w and ch >= 0.99 * h:
                    continue
                if area > max_area:
                    max_area = area
                    best_box = (x, y, cw, ch)

    if best_box is not None:
        x, y, cw, ch = best_box
        return warped_img[y:y+ch, x:x+cw]

    return warped_img



def _find_card_via_contour(img):
    """
    Finds the card via Canny edge detection + dilation + contour analysis.
    Works best when the card is on a clearly different (dark) background.
    Returns (xmin, ymin, xmax, ymax) or None.
    """
    h_img, w_img = img.shape[:2]
    img_area = h_img * w_img
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)

    candidates = []

    v_median = np.median(blurred)
    lower = int(max(0, 0.5 * v_median))
    upper = int(min(255, 1.5 * v_median))
    edges = cv2.Canny(blurred, lower, upper)

    for dilation_iter in [3, 5, 8]:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        dilated = cv2.dilate(edges, kernel, iterations=dilation_iter)
        dilated = cv2.morphologyEx(
            dilated, cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15)),
        )

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            area = cv2.contourArea(c)
            if area < 0.10 * img_area or area > 0.92 * img_area:
                continue
            x, y, w, h = cv2.boundingRect(c)
            if w > 0.92 * w_img and h > 0.85 * h_img:
                continue

            bbox_area = w * h
            solidity = area / bbox_area if bbox_area > 0 else 0
            aspect = max(w, h) / max(min(w, h), 1)
            if aspect < 1.2 or aspect > 2.5:
                continue
            if solidity < 0.7:
                continue

            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            vertex_bonus = 1.4 if len(approx) == 4 else (1.15 if len(approx) <= 6 else 1.0)
            score = area * (solidity ** 2) * vertex_bonus
            candidates.append({"box": (x, y, x + w, y + h), "score": score})

    # Also try OTSU threshold
    _, otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(otsu, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        area = cv2.contourArea(c)
        if area < 0.10 * img_area or area > 0.92 * img_area:
            continue
        x, y, w, h = cv2.boundingRect(c)
        if w > 0.92 * w_img and h > 0.85 * h_img:
            continue
        bbox_area = w * h
        solidity = area / bbox_area if bbox_area > 0 else 0
        aspect = max(w, h) / max(min(w, h), 1)
        if aspect < 1.2 or aspect > 2.5:
            continue
        if solidity < 0.7:
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        vertex_bonus = 1.4 if len(approx) == 4 else (1.15 if len(approx) <= 6 else 1.0)
        score = area * (solidity ** 2) * vertex_bonus
        candidates.append({"box": (x, y, x + w, y + h), "score": score})

    if candidates:
        candidates.sort(key=lambda c: c["score"], reverse=True)
        return candidates[0]["box"]
    return None


# ---------------------------------------------------------------------------
# Method 2: GrabCut + Asymmetric Edge-Density Expansion
# ---------------------------------------------------------------------------
def _grabcut_with_expansion(img, top_candidate: Optional[DocumentCandidate] = None):
    """
    Uses GrabCut to segment the card from the background, then expands
    the detected region using edge density to capture footer/header areas
    that GrabCut may miss (red banner, Aadhaar number line, etc.).

    Asymmetric expansion:
      - Upward:   conservative (backgrounds tend to bleed above)
      - Downward: aggressive   (capture Aadhaar number + footer banner)
      - Left/Right: moderate

    Returns (xmin, ymin, xmax, ymax) or None.
    """
    h_img, w_img = img.shape[:2]

    # --- Edge/Candidate Directed GrabCut Initialisation ---
    if top_candidate is not None:
        x, y, w, h = top_candidate.bounding_box
        pad_x = int(w * 0.05)
        pad_y = int(h * 0.05)
        xmin = max(0, x - pad_x)
        ymin = max(0, y - pad_y)
        xmax = min(w_img, x + w + pad_x)
        ymax = min(h_img, y + h + pad_y)
        rect = (xmin, ymin, xmax - xmin, ymax - ymin)
    else:
        # Dynamic edge density projection profiling
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        v_median = np.median(blurred)
        edges = cv2.Canny(blurred, int(max(0, 0.5 * v_median)), int(min(255, 1.5 * v_median)))

        row_sums = np.sum(edges, axis=1)
        col_sums = np.sum(edges, axis=0)

        active_rows = np.where(row_sums > 0.02 * np.max(row_sums))[0] if np.max(row_sums) > 0 else []
        active_cols = np.where(col_sums > 0.02 * np.max(col_sums))[0] if np.max(col_sums) > 0 else []

        if len(active_rows) > 0 and len(active_cols) > 0:
            ymin, ymax = active_rows[0], active_rows[-1]
            xmin, xmax = active_cols[0], active_cols[-1]
            pad_x = int((xmax - xmin) * 0.05)
            pad_y = int((ymax - ymin) * 0.05)
            xmin = max(0, xmin - pad_x)
            ymin = max(0, ymin - pad_y)
            xmax = min(w_img, xmax + pad_x)
            ymax = min(h_img, ymax + pad_y)
            rect = (xmin, ymin, xmax - xmin, ymax - ymin)
        else:
            # Fall back to 8% margin if no edge concentration found
            margin_x = int(w_img * 0.08)
            margin_y = int(h_img * 0.08)
            rect = (margin_x, margin_y, w_img - 2 * margin_x, h_img - 2 * margin_y)

    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    # Downscale for speed (GrabCut is O(n^2))
    scale = 1.0
    if max(h_img, w_img) > 800:
        scale = 800.0 / max(h_img, w_img)
        small = cv2.resize(img, None, fx=scale, fy=scale)
        small_mask = np.zeros(small.shape[:2], np.uint8)
        small_rect = (
            int(rect[0] * scale), int(rect[1] * scale),
            int(rect[2] * scale), int(rect[3] * scale),
        )
        cv2.grabCut(small, small_mask, small_rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
        mask = cv2.resize(small_mask, (w_img, h_img), interpolation=cv2.INTER_NEAREST)
    else:
        mask = np.zeros((h_img, w_img), np.uint8)
        cv2.grabCut(img, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)

    fg_mask = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)
    k_close = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, k_close)

    contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)
    if area < 0.05 * (h_img * w_img):
        return None

    gx, gy, gw, gh = cv2.boundingRect(largest)
    gc_x1, gc_y1, gc_x2, gc_y2 = gx, gy, gx + gw, gy + gh

    # --- Edge-density expansion ---
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    v_median = np.median(blurred)
    edges = cv2.Canny(blurred, int(max(0, 0.5 * v_median)), int(min(255, 1.5 * v_median)))

    row_sums = np.sum(edges, axis=1).astype(np.float64)
    col_sums = np.sum(edges, axis=0).astype(np.float64)

    sw = max(3, int(min(h_img, w_img) * 0.015))
    if sw % 2 == 0:
        sw += 1
    row_sums = np.convolve(row_sums, np.ones(sw) / sw, mode="same")
    col_sums = np.convolve(col_sums, np.ones(sw) / sw, mode="same")

    inner_row_avg = np.mean(row_sums[gc_y1:gc_y2]) if gc_y2 > gc_y1 else 0
    inner_col_avg = np.mean(col_sums[gc_x1:gc_x2]) if gc_x2 > gc_x1 else 0

    # Asymmetric thresholds
    up_thresh = inner_row_avg * 0.25       # Conservative upward
    down_thresh = inner_row_avg * 0.10     # Aggressive downward
    left_thresh = inner_col_avg * 0.15     # Moderate
    right_thresh = inner_col_avg * 0.15    # Moderate

    # Expansion caps (% of GrabCut box size)
    max_up = int(gh * 0.15)
    max_down = int(gh * 0.40)
    max_left = int(gw * 0.15)
    max_right = int(gw * 0.15)

    # Expand upward
    new_y1 = gc_y1
    for y in range(gc_y1 - 1, max(0, gc_y1 - max_up) - 1, -1):
        if row_sums[y] > up_thresh:
            new_y1 = y
        else:
            break

    # Expand downward
    new_y2 = gc_y2
    for y in range(gc_y2, min(h_img, gc_y2 + max_down)):
        if row_sums[y] > down_thresh:
            new_y2 = y
        else:
            break

    # Expand left
    new_x1 = gc_x1
    for x in range(gc_x1 - 1, max(0, gc_x1 - max_left) - 1, -1):
        if col_sums[x] > left_thresh:
            new_x1 = x
        else:
            break

    # Expand right
    new_x2 = gc_x2
    for x in range(gc_x2, min(w_img, gc_x2 + max_right)):
        if col_sums[x] > right_thresh:
            new_x2 = x
        else:
            break

    # Reject if expansion covers the entire image
    if (new_x2 - new_x1) > 0.95 * w_img and (new_y2 - new_y1) > 0.95 * h_img:
        return (gc_x1, gc_y1, gc_x2, gc_y2)

    return (new_x1, new_y1, new_x2, new_y2)


# ---------------------------------------------------------------------------
# Crop validation and helper logic
# ---------------------------------------------------------------------------
def _validate_crop_box(img, box, w_img, h_img):
    """
    Validates if a crop box represents a valid card sub-region.
    Prevents cropping already-cropped/full-image cards or matching
    small features (like faces, signatures, text blocks).
    """
    if box is None:
        return False
    x1, y1, x2, y2 = box
    w = x2 - x1
    h = y2 - y1
    area = w * h
    img_area = w_img * h_img

    # 1. Input image is already card-shaped and small-res
    # (very common for scanned cards or pre-cropped images)
    input_aspect = max(w_img, h_img) / max(min(w_img, h_img), 1)
    if 1.35 <= input_aspect <= 1.65 and img_area < 780000:
        return False

    # 2. Area must be substantial (at least 20% of image area)
    # This prevents cropping to small sub-regions like faces/signatures.
    if area < 0.20 * img_area:
        return False

    # 3. Aspect ratio must look like a card (1.25 to 2.2)
    aspect = max(w, h) / max(min(w, h), 1)
    if aspect < 1.25 or aspect > 2.2:
        return False

    # 4. Discarded edge density check:
    # If the outer region contains text/details (high edge density), we are cutting into the card.
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    v_median = np.median(blurred)
    edges = cv2.Canny(blurred, int(max(0, 0.5 * v_median)), int(min(255, 1.5 * v_median)))

    box_mask = np.zeros_like(edges)
    box_mask[y1:y2, x1:x2] = 255
    inner_edges = np.sum((edges > 0) & (box_mask == 255))
    outer_edges = np.sum(edges > 0) - inner_edges
    outer_area = img_area - area
    outer_density = outer_edges / outer_area if outer_area > 0 else 0

    if outer_density > 0.012:
        return False

    # 5. Already cropped checks: if the box occupies almost the full image
    w_ratio = w / w_img
    h_ratio = h / h_img
    if w_ratio > 0.92 and h_ratio > 0.88:
        return False

    return True


# ---------------------------------------------------------------------------
# Public API  —  unified card detection pipeline
# ---------------------------------------------------------------------------
def crop_via_opencv(img_path, padding_ratio=0.02):
    """
    Detects document boundary using the improved multi-candidate TDD pipeline:
      1. Preprocess image (Gray + Canny Edges)
      2. Extract candidate contours using tree hierarchy (cv2.RETR_TREE)
      3. Compute normalized weighted scoring and edge support
      4. Validate candidates to discard internal details or bad shapes
      5. Try perspective warping and second-pass refinement on the top 10 valid candidates
      6. Fall back to edge-directed GrabCut if no candidate passes
    """
    img = cv2.imread(img_path)
    if img is None:
        return None

    h_img, w_img = img.shape[:2]
    img_area = h_img * w_img

    # Check 1: Already card-shaped and low-res check (prevents double cropping)
    input_aspect = max(w_img, h_img) / max(min(w_img, h_img), 1)
    if 1.35 <= input_aspect <= 1.65 and img_area < 780000:
        logger.info(f"Image {os.path.basename(img_path)} is already card-shaped and low-res. Skipping crop.")
        return None

    # Setup Debug mode
    debug_mode = os.environ.get("AUTOCROP_DEBUG", "False").lower() == "true"
    debug_dir = None
    if debug_mode:
        base_dir = os.path.dirname(img_path)
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        debug_dir = os.path.join(base_dir, f"autocrop_debug_{base_name}")
        os.makedirs(debug_dir, exist_ok=True)
        cv2.imwrite(os.path.join(debug_dir, "01_original.png"), img)

    cfg = DocumentConfig()

    # Stage A: Preprocessing
    gray, edges = preprocess_image(img)
    if debug_mode:
        cv2.imwrite(os.path.join(debug_dir, "02_gray.png"), cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
        cv2.imwrite(os.path.join(debug_dir, "03_blur.png"), gray)
        cv2.imwrite(os.path.join(debug_dir, "04_edges.png"), edges)

        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        cv2.imwrite(os.path.join(debug_dir, "05_threshold.png"), otsu)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        dilated = cv2.dilate(edges, kernel, iterations=5)
        dilated = cv2.morphologyEx(dilated, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15)))
        cv2.imwrite(os.path.join(debug_dir, "06_morphology.png"), dilated)

    # Stage B: Find Candidate Contours
    candidates = find_candidate_contours(img, edges)

    # Stage C: Score Candidates
    candidates = score_candidates(candidates, cfg, edges)

    # Stage D: Validate Candidates
    candidates = validate_candidates(candidates, cfg, img, edges)

    # Log report
    log_candidate_report(candidates, cfg)

    if debug_mode:
        contours_img = img.copy()
        for idx, c in enumerate(candidates[:20]):
            color = (0, 255, 0) if c.is_valid else (0, 0, 255)
            cv2.drawContours(contours_img, [c.contour], -1, color, 2)
            x, y, w, h = c.bounding_box
            cv2.putText(contours_img, f"#{idx+1} ({c.score:.2f})", (x, y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
        cv2.imwrite(os.path.join(debug_dir, "07_contours.png"), contours_img)
        save_candidate_scores_png(candidates[:15], os.path.join(debug_dir, "08_candidate_scores.png"))

    # Stage E: Multi-candidate evaluation loop
    selected_candidate = None
    final_cropped = None

    valid_candidates = [c for c in candidates if c.is_valid]

    # Try warping and second-pass refining of the top 10 candidates
    for cand in valid_candidates[:10]:
        try:
            warped = warp_candidate(img, cand)
            if warped is not None:
                refined = refine_crop(warped)

                rh, rw = refined.shape[:2]
                aspect = max(rw, rh) / max(min(rw, rh), 1)
                if 1.25 <= aspect <= 2.2:
                    selected_candidate = cand
                    final_cropped = refined
                    break
        except Exception as e:
            logger.warning(f"Error processing candidate perspective: {e}")
            continue

    # If warping failed or no valid candidates found, fall back to GrabCut
    gc_box = None
    if final_cropped is None:
        logger.info("OpenCV contour candidates failed validation or warp. Falling back to GrabCut...")

        top_cand = candidates[0] if len(candidates) > 0 else None
        gc_box = _grabcut_with_expansion(img, top_cand)

        if gc_box is not None and _validate_crop_box(img, gc_box, w_img, h_img):
            x1, y1, x2, y2 = gc_box
            final_cropped = img[y1:y2, x1:x2]
            logger.info("GrabCut + expansion successfully localized crop box.")

    if final_cropped is None:
        return None

    # If GrabCut was used, apply padding and return coordinates
    if selected_candidate is None and gc_box is not None:
        x1, y1, x2, y2 = gc_box
        bw = x2 - x1
        bh = y2 - y1
        pw = int(padding_ratio * bw)
        ph = int(padding_ratio * bh)
        x1 = max(0, x1 - pw)
        y1 = max(0, y1 - ph)
        x2 = min(w_img, x2 + pw)
        y2 = min(h_img, y2 + ph)

        if debug_mode:
            cv2.imwrite(os.path.join(debug_dir, "10_grabcut_mask.png"), edges)
            cv2.imwrite(os.path.join(debug_dir, "12_final.png"), img[y1:y2, x1:x2])

        return (x1, y1, x2, y2)

    # If perspective warped, save directly and return sentinel (0, 0, 0, 0)
    if final_cropped is not None and selected_candidate is not None:
        if debug_mode:
            sel_img = img.copy()
            cv2.drawContours(sel_img, [selected_candidate.contour], -1, (0, 255, 0), 3)
            cv2.imwrite(os.path.join(debug_dir, "09_selected_candidate.png"), sel_img)
            cv2.imwrite(os.path.join(debug_dir, "11_warped.png"), warp_candidate(img, selected_candidate))
            cv2.imwrite(os.path.join(debug_dir, "12_final.png"), final_cropped)

        # Make backup of original file
        backup_path = img_path + ".original"
        if not os.path.exists(backup_path):
            shutil.copy2(img_path, backup_path)

        # Save warped crop directly to disk
        cv2.imwrite(img_path, final_cropped)
        return (0, 0, 0, 0)

    return None





# ---------------------------------------------------------------------------
# Main entry point called from the ingestion pipeline
# ---------------------------------------------------------------------------
def autocrop_image_if_aadhar(filepath: str) -> None:
    # Ensure file exists and is an image
    _, ext = os.path.splitext(filepath.lower())
    if ext not in ['.jpg', '.jpeg', '.png']:
        return
        
    if filepath.endswith('.original'):
        return

    try:
        img = Image.open(filepath)
        img_width, img_height = img.size
        
        if img_width < 100 or img_height < 100:
            return

        # 1. Try local OpenCV cropper first
        crop_box = crop_via_opencv(filepath, padding_ratio=0.02)
        if crop_box is not None:
            if crop_box == (0, 0, 0, 0):
                logger.info(f"Local OpenCV cropper successfully perspective-warped and cropped card for {os.path.basename(filepath)}")
                return
            xmin, ymin, xmax, ymax = crop_box
            logger.info(f"Local OpenCV cropper successfully localized card for {os.path.basename(filepath)}")
            
            # Save original backup
            backup_path = filepath + ".original"
            if not os.path.exists(backup_path):
                shutil.copy2(filepath, backup_path)
                
            cropped_img = img.crop((xmin, ymin, xmax, ymax))
            cropped_img.save(filepath, "JPEG", quality=95)
            return

        # 2. Fallback to VLM if local cropper did not find a sub-region
        logger.info(f"OpenCV could not localize sub-region for {os.path.basename(filepath)}. Falling back to VLM...")
        
        ai_client = AIClient(api_keys=DEFAULT_GEMINI_API_KEYS)

        system_instruction = (
            "You are an expert document localization tool. Your job is to locate the absolute outer boundaries of the entire Aadhaar card. "
            "The Aadhaar card contains several key elements: a photo (usually on the left), personal text details (name, DOB, gender), "
            "a 12-digit Aadhaar number (at the bottom), a bottom tricolor or red banner, and a QR code (usually on the right). "
            "Your bounding box must be a single rectangle that fully encapsulates all of these elements: "
            "1. ymin must be placed just above the top header ('Government of India' / 'भारत सरकार' and the emblem). "
            "2. ymax must be placed just below the bottom red/tricolor banner and the bottom-most text/Aadhaar number. "
            "3. xmin must be placed just to the left of the photo/emblem. "
            "4. xmax must be placed just to the right of the QR code/card border. "
            "Do not crop inside the card or cut off the Aadhaar number or QR code. Crop exactly at the outer white edges of the card, leaving no surrounding background. "
            "Return the output ONLY as a valid JSON object with these exact keys: "
            "{\"has_aadhar\": true/false, \"ymin\": int, \"xmin\": int, \"ymax\": int, \"xmax\": int}"
        )

        res = ai_client.generate_json(
            system_instruction=system_instruction,
            user_prompt=[img, "Locate the entire Aadhaar card encapsulating all headers, footers, Aadhaar number, photo, and QR code, cropping exactly to the outer borders."],
            model="gemini-2.5-flash"
        )
        
        if "text" in res:
            text = res["text"].strip()
            if text.startswith("```"):
                text = "\n".join(text.split("\n")[1:-1])
            res = json.loads(text)

        if res.get("has_aadhar") and all(k in res for k in ["ymin", "xmin", "ymax", "xmax"]):
            ymin_raw = res["ymin"]
            xmin_raw = res["xmin"]
            ymax_raw = res["ymax"]
            xmax_raw = res["xmax"]

            ymin = max(0, int(ymin_raw * img_height / 1000))
            xmin = max(0, int(xmin_raw * img_width / 1000))
            ymax = min(img_height, int(ymax_raw * img_height / 1000))
            xmax = min(img_width, int(xmax_raw * img_width / 1000))

            if (xmax - xmin) < 50 or (ymax - ymin) < 50:
                logger.warning(f"Detected crop box for {os.path.basename(filepath)} is too small. Skipping crop.")
                return

            backup_path = filepath + ".original"
            if not os.path.exists(backup_path):
                shutil.copy2(filepath, backup_path)

            cropped_img = img.crop((xmin, ymin, xmax, ymax))
            cropped_img.save(filepath, "JPEG", quality=95)
            logger.info(f"Successfully auto-cropped Aadhaar card via VLM fallback for {os.path.basename(filepath)}")

    except Exception as e:
        logger.error(f"Error during autocropping for {os.path.basename(filepath)}: {e}")
