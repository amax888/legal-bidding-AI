# Kiểm tra tuân thủ PCCC và mật độ xây dựng dựa trên quy chuẩn (có dùng RAG để lấy ngữ cảnh)
from typing import List, Optional, Callable
from dataclasses import dataclass, field

@dataclass
class PCCCInput:
    """Thông số hồ sơ thiết kế liên quan PCCC."""
    so_tang: int = 0
    chieu_cao_m: float = 0.0
    dien_tich_san_moi_tang_m2: float = 0.0
    so_loi_thoat: int = 0
    chieu_rong_loi_thoat_m: float = 0.0
    khoang_cach_xa_nhat_den_cua_thoat_m: float = 0.0
    co_sprinkler: bool = False
    loai_nha: str = "nhà ở"  # nhà ở, công cộng, ...

@dataclass
class DensityInput:
    """Thông số hồ sơ liên quan mật độ xây dựng."""
    dien_tich_lot_m2: float = 0.0
    dien_tich_xay_dung_m2: float = 0.0
    tong_dien_tich_san_m2: float = 0.0
    so_tang: int = 0

@dataclass
class ComplianceResult:
    """Kết quả kiểm tra tuân thủ."""
    passed: bool
    message: str
    details: List[str] = field(default_factory=list)
    references: List[dict] = field(default_factory=list)

def check_pccc_compliance(
    inp: PCCCInput,
    retriever: Optional[Callable[[str], List[dict]]] = None,
) -> ComplianceResult:
    """Kiểm tra tuân thủ PCCC dựa trên quy chuẩn (QCVN 06, ...)."""
    details = []
    refs = []

    if retriever:
        docs = retriever("PCCC lối thoát nạn sprinkler chiều rộng khoảng cách")
        refs = [{"content": d.get("content", ""), "source": d.get("source", "")} for d in docs[:3]]

    # Số lối thoát
    if inp.so_tang >= 3 or inp.dien_tich_san_moi_tang_m2 > 300:
        if inp.so_loi_thoat < 2:
            details.append("Nhà từ 3 tầng trở lên hoặc diện tích sàn một tầng > 300 m² cần ít nhất 2 lối thoát nạn độc lập.")
        else:
            details.append("Đạt yêu cầu số lối thoát nạn (≥ 2).")
    if inp.so_loi_thoat >= 1 and inp.chieu_rong_loi_thoat_m < 1.0:
        details.append("Chiều rộng lối thoát nạn tối thiểu 1,0 m (nhà ở) hoặc 1,2 m (công cộng).")

    # Khoảng cách đến cửa thoát
    max_dist = 30.0 if inp.co_sprinkler else 20.0
    if inp.khoang_cach_xa_nhat_den_cua_thoat_m > max_dist:
        details.append(f"Khoảng cách từ điểm xa nhất đến cửa thoát nạn không quá {max_dist:.0f} m (có sprinkler: 30 m, không: 20 m).")

    # Chiều cao và sprinkler
    if inp.chieu_cao_m >= 28:
        if not inp.co_sprinkler:
            details.append("Nhà cao từ 28 m trở lên bắt buộc có hệ thống chữa cháy tự động (sprinkler).")
        else:
            details.append("Đạt yêu cầu hệ thống chữa cháy cho nhà cao ≥ 28 m.")

    passed = not any("cần" in d or "bắt buộc" in d or "không quá" in d for d in details if "Đạt" not in d)
    # Đơn giản: nếu có dòng lỗi (không phải "Đạt") thì chưa pass
    errors = [d for d in details if "Đạt" not in d and ("cần" in d or "bắt buộc" in d or "tối thiểu" in d or "không quá" in d)]
    passed = len(errors) == 0
    message = "Hồ sơ đáp ứng các yêu cầu PCCC đã kiểm tra." if passed else "Hồ sơ cần bổ sung/điều chỉnh để đáp ứng quy chuẩn PCCC."
    return ComplianceResult(passed=passed, message=message, details=details, references=refs)

def check_density_compliance(
    inp: DensityInput,
    retriever: Optional[Callable[[str], List[dict]]] = None,
) -> ComplianceResult:
    """Kiểm tra mật độ xây dựng và hệ số sử dụng đất."""
    details = []
    refs = []

    if retriever:
        docs = retriever("mật độ xây dựng thuần hệ số sử dụng đất FAR")
        refs = [{"content": d.get("content", ""), "source": d.get("source", "")} for d in docs[:3]]

    if inp.dien_tich_lot_m2 <= 0:
        return ComplianceResult(
            passed=False,
            message="Chưa nhập diện tích lô đất.",
            details=["Vui lòng nhập diện tích lô đất (m²)."],
            references=refs,
        )

    # Mật độ thuần = diện tích xây dựng / diện tích lô
    mat_do_thuan = (inp.dien_tich_xay_dung_m2 / inp.dien_tich_lot_m2 * 100) if inp.dien_tich_lot_m2 else 0

    limits = [
        (100, 90),
        (200, 80),
        (300, 70),
        (500, 60),
    ]
    max_mat_do = 90
    for limit_area, pct in limits:
        if inp.dien_tich_lot_m2 <= limit_area:
            max_mat_do = pct
            break
    if inp.dien_tich_lot_m2 > 500:
        max_mat_do = 60

    if mat_do_thuan > max_mat_do:
        details.append(f"Mật độ xây dựng thuần {mat_do_thuan:.1f}% vượt mức tối đa {max_mat_do}% cho lô đất {inp.dien_tich_lot_m2:.0f} m².")
    else:
        details.append(f"Mật độ xây dựng thuần {mat_do_thuan:.1f}% trong giới hạn (tối đa {max_mat_do}%).")

    # FAR = tổng diện tích sàn / diện tích lô (giả sử FAR max 3.5 cho nhà ở)
    if inp.tong_dien_tich_san_m2 > 0 and inp.dien_tich_lot_m2 > 0:
        far = inp.tong_dien_tich_san_m2 / inp.dien_tich_lot_m2
        far_max = 3.5
        if far > far_max:
            details.append(f"Hệ số sử dụng đất FAR = {far:.2f} vượt mức tham khảo {far_max} (cần kiểm tra quy chế địa phương).")
        else:
            details.append(f"FAR = {far:.2f} trong giới hạn tham khảo.")

    errors = [d for d in details if "vượt" in d]
    passed = len(errors) == 0
    message = "Hồ sơ đáp ứng chỉ tiêu mật độ xây dựng đã kiểm tra." if passed else "Hồ sơ cần điều chỉnh mật độ/FAR theo quy định."
    return ComplianceResult(passed=passed, message=message, details=details, references=refs)
