# LUẬT MỚI — anh chốt 2026-10-19

> Các luật dưới đây **đã có hiệu lực ngay** từ file này + code. Phần chép vào `CLAUDE.md`
> đang chờ anh bấm duyệt (file đó là agent-instruction được bảo vệ).

---

## 0. MỌI CHỮ TIẾNG NHẬT PHẢI CÓ BẢN DỊCH TIẾNG VIỆT (anh chốt 2026-10-19)

**Không được để tiếng Nhật trần ở bất kỳ đâu** — báo cáo HTML, chat, sheet, log, jobs.json.

Quy ước in:

```
社会のなぜ研究室
→ Phòng nghiên cứu "vì sao" của xã hội
```

- Bản Nhật gốc **vẫn phải giữ** (máy 1 dùng để đăng video), nhưng luôn kèm dòng dịch bên dưới.
- Trong HTML: `<span class="jp">bản Nhật</span><br><span class="vi">→ bản Việt</span>`.
- Dùng `viral_hunt\translate.py :: translate_many()` — dịch theo lô, 1 call cho ~60 chuỗi.
- Không dịch được thì in tag **`chưa dịch được`** — KHÔNG bỏ qua, KHÔNG bịa nghĩa.
- Handle romaji (`@shakai-no-naze`) không phải tiếng Nhật thì giữ nguyên, không gắn tag.
- Áp cho cả `title_jp`, `thumbnail_jp`, `cau_hoi_cuoi` do LLM sinh ra.

---

## 1. ĐƯỜNG DẪN PHẢI ĐẦY ĐỦ TUYỆT ĐỐI

**Mọi đường dẫn file/thư mục trong báo cáo, chat, sheet, log đều phải ghi ĐẦY ĐỦ TUYỆT ĐỐI.**
Cấm viết tắt, cấm cắt gọn, cấm dùng `...`, cấm chỉ ghi tên file trơn.

```
ĐÚNG:  E:\CLAUDE\YOUTUBE\FlowHandoff_local\results\VIRAL_2026-10-19.html
SAI:   ...\results\VIRAL_2026-10-19.html
SAI:   results\VIRAL_2026-10-19.html
SAI:   VIRAL_2026-10-19.html
SAI:   reports\viral_hunt\<ngày>\jobs.json
```

Lý do: anh mở file bằng cách copy đường dẫn; đường dẫn cắt gọn là không dùng được.

Áp dụng cho:
- đường dẫn trong HTML báo cáo (mục "Cách máy 1 / h2dev dùng báo cáo này")
- cột NOTE của Google Sheet
- mọi câu trả lời trong chat
- log của tool

---

## 2. BÁO CÁO VIRAL HẰNG NGÀY → TAB `NOTE`, Ô `C21` (KHOÁ CỐ ĐỊNH)

Tool `viral_hunt` mỗi ngày ghi đường dẫn báo cáo vào **tab `NOTE`, ô `C21`**.

- **KHOÁ CỐ ĐỊNH Ô NÀY** — ngày sau ĐÈ LÊN ngày trước. Không thêm dòng, không đổi ô, không append.
- Ô `B21` có nhãn sẵn `BÁO CÁO NGÀY`; `C21` là giá trị.
- **Nội dung ô C21 = đường dẫn NHÌN TỪ MÁY 1** (nơi anh mở file), KHÔNG phải đường dẫn trên
  máy 2 chạy tool:

  ```
  E:\CLAUDE\YOUTUBE\h2dev\FlowHandoff_local\results\VIRAL_<YYYY-MM-DD>.html
  ```

  Máy 2 ghi file thật ở `E:\CLAUDE\YOUTUBE\FlowHandoff_local\results\` rồi
  `sheet_note.path_for_may1()` đổi gốc sang `h2dev\FlowHandoff_local\results` trước khi ghi sheet.
  Hàm **không** kiểm `os.path.exists` trên đường dẫn máy 1 — file nằm ở máy khác, kiểm sẽ báo sai.

- Ghi tự động ở cuối mỗi lần `viral_hunt\run_daily.py` chạy thành công.
- Ghi tay: `py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\viral_hunt\sheet_note.py --path "<đường dẫn máy 1>"`
- Đổi gốc thư mục máy 1: sửa hằng `MAY1_RESULTS_DIR` trong
  `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\viral_hunt\sheet_note.py`
- Ghi sheet lỗi ⇒ **phải báo rõ lỗi** trong log + chat, không được im lặng bỏ qua.

Sheet: `1xu4iNudIPanWrUxlTODqIySGf9YxLy7rpTq9OtXDMOU` · tab `NOTE` · ô `C21`.

---

## Việc còn lại (cần anh duyệt)

Chép nguyên 2 mục trên vào `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\CLAUDE.md`,
đặt ngay sau mục `## Định dạng báo cáo`. File CLAUDE.md là agent-instruction được bảo vệ
nên lệnh ghi bị chặn chờ anh bấm duyệt.
