# -*- coding: utf-8 -*-
"""lanes.py — CÔNG THỨC WIN của 4 lane, chép từ 4 báo cáo WIN 2026-10-16.

Nguồn (đọc lại khi cần đối chiếu):
  E:\\CLAUDE\\YOUTUBE\\FlowHandoff_local\\results\\BAO_CAO_WIN_LANE_L_2026-10-16.html
  E:\\CLAUDE\\YOUTUBE\\FlowHandoff_local\\results\\BAO_CAO_WIN_LANE_M_2026-10-16.html
  E:\\CLAUDE\\YOUTUBE\\FlowHandoff_local\\results\\BAO_CAO_WIN_LANE_N_2026-10-16.html
  E:\\CLAUDE\\YOUTUBE\\FlowHandoff_local\\results\\BAO_CAO_WIN_LANE_O_2026-10-16.html

Mỗi lane gồm:
  win_one_line  — câu chốt công thức (in vào đầu mục của lane trong báo cáo)
  win_zone      — vùng chủ đề ĐƯỢC làm
  lose_zone     — vùng chủ đề ĐÃ THUA (dùng để trừ điểm)
  topics_win / topics_lose / topics_soft — từ khoá chấm điểm (title nặng gấp 2 lần description)
  title_pat     — khuôn tiêu đề thắng (regex)
  keywords      — từ khoá dùng để QUÉT YouTube (mỗi từ 1 call search = 100 unit)
  draft_rule    — luật sinh đề bài khi KHÔNG có LLM (khung xương, không bịa nội dung)
  bad_format    — dấu hiệu SAI định dạng so với kênh mình (trừ điểm mạnh)

KHÔNG sửa số ở đây mà không đọc lại báo cáo WIN tương ứng.
"""

LANES = {
    # ------------------------------------------------------------------ LANE L
    "L": {
        "tab": "L-shakai-no-naze",
        "channel": "社会のなぜ研究室",
        "handle": "@shakai-no-naze",
        "win_one_line": (
            "「một NHÓM NGƯỜI cụ thể làm một HÀNH VI trái lẽ thường」 × "
            "「cơ chế vô hình khiến lỗi không thuộc về họ, có tên + có số」 × "
            "「trục đối lập ai cũng muốn nói một câu (nam–nữ, quản lý–nhân viên, thế hệ)」"
        ),
        "win_zone": [
            "婚活・結婚・男女 (婚活男性, 結婚相談所, マッチングアプリ)",
            "Công sở × thế hệ (出世, 管理職/課長, 静かな退職, Z世代, 若手)",
        ],
        "lose_zone": [
            "Giảng số liệu vĩ mô (給料30年, 手取り) — thân bài thành bài giảng, APV 14,8%",
            "Tâm lý trừu tượng (責任感, 人の目, 本音) — YouTube không tìm được khán giả",
        ],
        "topics_win": ["婚活", "結婚相談所", "マッチングアプリ", "お見合い", "婚活男性",
                       "出世", "管理職", "課長", "主任", "静かな退職", "Z世代", "若手",
                       "転勤", "カスハラ", "年賀状", "昇格", "部下"],
        "topics_lose": ["給料 統計", "手取り", "国税庁", "平均年収", "人の目", "責任感",
                        "本音", "自己肯定感", "幸せですか"],
        "core_win": ["婚活", "結婚", "お見合い", "マッチング", "出世", "管理職", "課長",
                     "主任", "静かな退職", "Z世代", "若手", "昇進", "転勤", "カスハラ"],
        "topics_soft": ["50代", "定年", "夫婦", "義父", "嫁"],
        "title_pat": [r"なぜ.+?(理由|のか)", r"【漫画】.+?(理由|末路|実態|正体)",
                      r"「.+?」が.+?(理由|末路)", r"\d+(\.\d+)?%"],
                "keywords": [
            "漫画 婚活",            "漫画 結婚相談所",            "漫画 マッチングアプリ",            "漫画 婚活 男性",
            "漫画 婚活 女",            "漫画 お見合い",            "漫画 婚活 現実",            "漫画 結婚 できない",
            "漫画 婚活 末路",            "漫画 出世",            "漫画 静かな退職",            "漫画 Z世代",
            "漫画 課長",            "漫画 管理職",            "漫画 職場 若手",            "漫画 主任",
            "漫画 転勤",            "漫画 カスハラ",            "漫画 昇進",            "漫画 職場 世代",
            "マンガ 婚活",            "マンガ 職場",            "婚活 漫画",            "職場 漫画",
            "出世 漫画",            "静かな退職 漫画",            "Z世代 漫画",            "管理職 漫画",
            "婚活 スカッと",            "職場 スカッと 漫画",
        ],
        "draft_rule": (
            "Tiêu đề 1 vế ≤30 ký tự, dạng 「[nhóm người] が [hành vi lạ] 理由【漫画】」. "
            "Hook 3 câu đầu: thoại của người có quyền/chuyên gia lật giả định + 1 con số "
            "(「問題は○○じゃないんです」「今月も、お申し込みは0件」). "
            "Đáp án phải là CƠ CHẾ HỆ THỐNG có tên + có số, không phải lời khuyên tâm lý. "
            "Thumbnail chia đôi A ↔ B có số (0件 / ここにいたのに). "
            "Cuối tập để câu hỏi 2 phe để mời bình luận."
        ),
        "bad_format": [],
    },
    # ------------------------------------------------------------------ LANE N
    "N": {
        "tab": "Lane-N",
        "channel": "シニアのこれから",
        "handle": "@senior_kurashi60",
        "win_one_line": (
            "「定年後の仕事」× 「thiếu tiền CỤ THỂ mỗi tháng」× "
            "「nghề cũ 38–40 năm bị chỗ làm mới coi là số 0」— mỗi tập = MỘT nghề làm thêm có thật "
            "mà người 60+ đang cân nhắc (工場ライン, 清掃, 警備, 配送, 交通誘導, ホテル, 品出し, "
            "マンション管理人, 介護補助, スキマバイト)"
        ),
        "win_zone": [
            "Việc làm thêm sau hưu (đổi nhiều việc, thử từng nghề)",
            "シルバー人材センター / ハローワーク 65歳",
            "Nghèo + nhà ở/bảo lãnh (có con số tiền)",
        ],
        "lose_zone": [
            "Giá trị con người / họp lớp (人の価値、誰が決める？) — CTR 0,8%",
            "Gia đình, nhà cửa, di cư, viện dưỡng lão thuần — không có \"việc\" và \"tiền mình kiếm\"",
            "Mai mối tuổi già — thân bài tốt nhưng khán giả khác, YouTube thử ít",
        ],
        "topics_win": ["定年後", "シルバー人材センター", "ハローワーク", "再就職",
                       "バイト", "パート", "警備", "清掃", "品出し", "交通誘導",
                       "マンション管理人", "配送", "工場", "介護補助", "スキマバイト",
                       "65歳", "64歳", "66歳", "67歳", "時給"],
        "topics_lose": ["同窓会", "人の価値", "生きがいだけ", "老後の過ごし方",
                        "人間関係の3つ", "3つの落とし穴", "3つの盲点"],
        "topics_soft": ["年金", "退職金", "2000万"],
        "core_win": ["バイト", "シルバー人材", "ハローワーク", "警備", "清掃", "品出し",
                     "管理人", "配送", "交通誘導", "再就職", "仕事", "パート",
                     # thêm 2026-10-18: video 96.514 view / 5.840 sub
                     # 「働くシニアに密着…88歳で一人カフェ経営」và 20.400 view / 1.370 sub
                     # 「65歳で退職して1年」đều đúng ngách nhưng bị loại oan vì thiếu chữ 仕事.
                     "働く", "シニア", "退職", "定年", "年金"],
        "title_pat": [r"定年後", r"シルバー人材", r"ハローワーク",
                      r"(バイト|清掃|警備|品出し|管理人|配送|交通誘導)",
                      r"時給\d", r"\d+歳"],
                "keywords": [
            "定年後 バイト",            "定年後 仕事",            "シルバー人材センター",            "ハローワーク 65歳",
            "定年後 警備",            "定年後 清掃",            "定年後 品出し",            "定年後 マンション管理人",
            "60代 仕事",            "65歳 仕事",            "定年後 パート",            "年金 足りない 仕事",
            "60代 再就職",            "定年後 交通誘導",            "定年後 配送",            "定年後 ホテル バイト",
            "定年後 工場",            "定年後 介護補助",            "スキマバイト 60代",            "定年後 仕事 現実",
            "漫画 定年後",            "漫画 シルバー人材",            "漫画 定年後 仕事",            "60代 バイト 漫画",
            "定年後 警備員",            "定年後 清掃員",            "65歳 バイト",            "定年後 仕事 選び",
            "老後の仕事",            "シニア 仕事 漫画",
        ],
        "draft_rule": (
            "Đề = 定年後、［số tiền thiếu cụ thể］で［nghề mới cụ thể］を始めた［tuổi］の元［nghề cũ + số năm］. "
            "Tiêu đề nêu nghề + tuổi + tiền, kết bằng câu hỏi kết quả — KHÔNG dùng dạng 「3つの落とし穴／3つの盲点」. "
            "Hook giây 1: câu sỉ nhục về NĂNG LỰC LÀM VIỆC (「旗振るしか能がない」「元水道課なのに、水漏れひとつ直せないんですか？」). "
            "Thumbnail 2 khung trước/sau + đạo cụ nghề (求人票, cờ giao thông, mũ bảo hộ) + 1 con số tiền + 1 câu hỏi ≤10 chữ. "
            "Thân bài: mỗi nghề có 時給/giờ/độ mệt/ai hợp + 1 nhân vật đồng hành xuyên suốt (điểm yếu hiện tại APV 21,8%)."
        ),
        "bad_format": [],
    },
    # ------------------------------------------------------------------ LANE M
    "M": {
        "tab": "M-teinengo-anaba",
        "channel": "定年後の穴場ノート",
        "handle": "@teinengo-anaba",
        "win_one_line": (
            "「TIỀN bị cắt + PHẨM GIÁ bị chạm + MỘT QUYẾT ĐỊNH」: người 60+ bị chỗ làm lặng lẽ hạ giá "
            "theo tuổi, thể hiện bằng MỘT CON SỐ BỊ MẤT (ngày ca, điều kiện tái tuyển, lương hưu), "
            "rồi giữ phẩm giá bằng cách chọn đúng việc — format 7 hạng"
        ),
        "win_zone": [
            "再雇用 / ở lại hay ra đi khi công ty hạ điều kiện",
            "Thu nhập bị cắt lặng lẽ: シフト削減, 契約更新, giảm ngày công",
            "Lương hưu / quy định hiểu sai làm mất tiền thật (在職老齢年金, 扶養, 雇用保険 20h)",
        ],
        "lose_zone": [
            "Thiết kế thời gian thuần (週3日・午前だけ) — 398 view",
            "Tính cách (ít giao tiếp, dậy sớm) — không ai lấy mất gì của nhân vật",
            "Lọc việc theo điều kiện thuần (ngồi được, không cần bằng)",
        ],
        "topics_win": ["再雇用", "再雇用", "シフト", "契約更新", "在職老齢年金",
                       "給料", "減額", "日数", "週5", "雇い止め", "定年後", "63歳", "64歳",
                       "65歳", "7選", "穴場"],
        # Từ khoá LÕI: bắt buộc có ≥1 trong title thì mới coi là đúng ngách.
        # "年金" một mình quá rộng — đã nhận oan video "50代で結婚…年金と相続" (2026-10-18).
        # "定年後/同期/働く/辞める/60歳/65歳" thêm cùng ngày: video 1,2 triệu view
        # 「60歳で辞めるか、65歳まで働くか。同期2人が5年後に知った本当の正解」— đúng ngách
        # nhất của lane M (ở lại vs ra đi + 同期) mà bị loại oan vì không có chữ 再雇用.
        "core_win": ["再雇用", "シフト", "契約更新", "在職老齢年金", "給料", "雇い止め",
                     "減給", "減額", "7選", "穴場", "仕事", "定年後", "同期", "働く",
                     "辞める", "60歳", "65歳", "退職"],
        "topics_lose": ["午前だけ", "週3日", "朝活", "趣味", "静かな仕事", "通勤 だけ"],
        "topics_soft": ["同期", "妻", "夫"],
        "title_pat": [r"再雇用", r"シフト", r"年金", r"契約", r"\d+選",
                      r"「.+?」と言われた", r"給料"],
                "keywords": [
            "再雇用",            "定年後 再雇用",            "再雇用 給料 減った",            "再雇用 面談",
            "60代 シフト 減らされた",            "シフト削減 パート 60代",            "在職老齢年金",            "定年後 仕事 7選",
            "定年後 穴場 仕事",            "契約更新 60代",            "雇い止め 60代",            "働くと年金 減る",
            "63歳 仕事",            "64歳 仕事",            "65歳 雇い止め",            "定年後 給料 下がる",
            "再雇用 断った",            "再雇用 更新しない",            "漫画 再雇用",            "漫画 定年後 給料",
            "再雇用 漫画",            "定年後 仕事 漫画",            "60代 給料 漫画",            "再雇用 実態",
            "定年後 待遇",            "60歳 再雇用",            "65歳 再雇用",            "定年後 収入 減",
            "再雇用 手取り",            "シニア 再雇用 漫画",
        ],
        "draft_rule": (
            "Hook 0–30s: câu 1 là THOẠI của người có quyền (trẻ hơn, lịch sự) + con số mới; "
            "câu 2 cảnh (nhìn tablet/đồng hồ, không nhìn mặt); câu 3 田島 nêu con số cũ; "
            "câu 4 câu sỉ nhục lịch sự liên quan tuổi/lương hưu; câu 5 nội tâm có con số (年金まであと2年). "
            "Cú lật trước giây 60, hạng 7 bắt đầu trước ký tự ~900. "
            "Title: tuổi + quyết định + con số + 7選 (「再雇用を断った63歳が見つけた穴場の仕事7選」). "
            "Thumbnail: con số trước→sau (先月18日→来月11日) + 1 câu thoại sỉ nhục + mặt 田島; "
            "chữ trên thumbnail phải xuất hiện y nguyên trong kịch bản."
        ),
        "bad_format": [],
    },
    # ------------------------------------------------------------------ LANE O
    "O": {
        "tab": "Lane-O",
        "channel": "人生のつづき",
        "handle": "@人生のつづき",
        "win_one_line": (
            "「介護士 NGANG HÀNG có CÂU CỬA MIỆNG nghe rất hợp lý để né việc / tự đề cao」"
            "× 「một người hiền LẶNG LẼ GÁNH THAY, người xem thấy cái giá trước nhân vật」"
            "× 「hậu quả là MỘT HÌNH ẢNH NHỎ CỤ THỂ (tên biến khỏi bảng phân công, lần thứ 3, 12 phút trước giờ về)」"
        ),
        "win_zone": [
            "介護士 cùng ca, 25–45 tuổi, câu cửa miệng ai đi làm cũng từng nghe",
            "Câu né việc nghe có lý: 定時なんで / じゃあ、辞めます / それ、担当じゃない",
            "Câu tự đề cao: 自分、仕事できるんで / 私、間違えないんで / 前の施設ではこうでした",
        ],
        "lose_zone": [
            "Nhân vật là SẾP/giám đốc cơ sở (người xem không làm cùng ca) — ep04 thua",
            "Chuyện gia đình (義妹, 息子) — rời ngách công sở",
            "Câu ác ra mặt (そんなことも分からないの？) — chỉ ở mức GIỮA",
        ],
        "topics_win": ["口ぐせ", "口癖", "介護士", "介護", "同僚", "新人", "定時",
                       "担当", "職場", "施設", "スカッと", "ナースコール", "夜勤", "申し送り"],
        "topics_lose": ["施設長", "部長だった", "義妹", "義母", "嫁", "息子"],
        "topics_soft": ["退勤", "シフト", "主任", "利用者"],
        "core_win": ["介護", "口ぐせ", "口癖", "同僚", "職場", "新人", "定時", "担当",
                     "スカッと", "ナースコール", "夜勤"],
        "title_pat": [r"「.+?」が口ぐせ", r"「.+?」が口癖", r"介護", r"スカッと",
                      r"(末路|結果|その後|いた)"],
                "keywords": [
            "漫画 介護",            "漫画 介護士",            "スカッと 介護",            "口ぐせ 同僚",
            "漫画 職場 同僚",            "漫画 介護 職場",            "漫画 施設 職員",            "スカッと 職場",
            "漫画 定時",            "漫画 新人 介護",            "口ぐせ 介護士",            "漫画 夜勤 介護",
            "漫画 ナースコール",            "漫画 介護 人間関係",            "漫画 職場 新人",            "スカッと 同僚",
            "漫画 介護 先輩",            "漫画 特養",            "介護 漫画 スカッと",            "介護士 漫画",
            "介護職 漫画",            "同僚 口癖 漫画",            "職場 いじめ 漫画",            "介護 職場 トラブル 漫画",
            "漫画 デイサービス",            "漫画 介護施設",            "スカッと 介護士",            "漫画 申し送り",
            "介護 人間関係 漫画",            "職場 スカッと 漫画",
        ],
        "draft_rule": (
            "Tiêu đề = 【漫画】「câu cửa miệng」が口ぐせの介護士 + (…/が、) + cảnh/con số cụ thể + 結果…/いた. "
            "10 giây đầu là CÂU CỬA MIỆNG hoặc CẢNH HẬU QUẢ, không giới thiệu cơ sở trước. "
            "Thân: câu cửa miệng lặp 3 lần ở 3 bối cảnh, mỗi lần cái giá người khác trả tăng lên. "
            "Kết: (1) cho thấy RÕ nhân vật chính rốt cuộc ra sao — khán giả đòi; "
            "(2) câu đảo nghĩa câu cửa miệng từ miệng người khác; "
            "(3) 1 câu xin 高評価・チャンネル登録 + câu hỏi 「あなたの職場にもいましたか？」."
        ),
        "bad_format": [],
    },
}

# Từ khoá chung: format manga/faceless. Dùng để chấm "đúng định dạng như kênh mình".
MANGA_TITLE = r"(漫画|マンガ|まんが|AI漫画|コミック|アニメ|紙芝居)"
MANGA_ANY = r"(漫画|マンガ|まんが|AI漫画|コミック|紙芝居)"
# ゆっくり解説 = faceless nhưng KHÔNG phải manga của mình → chỉ cộng điểm nhẹ
SEMI_FORMAT = r"(ゆっくり解説|2ch|スレ|解説)"

# Kênh của chính mình — KHÔNG bao giờ đưa vào báo cáo
OWN_CHANNEL_IDS = {
    "UC9huXCiBIXBfUh11D7ZsFSA",   # Satori (đã bị đình chỉ)
    "UCYhbfP8greeTOL-0B_-OqLQ",   # A shinya
    "UCwdrP4WLHmmtYqf8QcxcFKg",   # E 70dai-kenko
    "UCIimxP275YufOXXIlu9y9Lg",   # F teinengo-real
    "UCk8E_FHIYjY7GN_qdpSKaMw",   # K yakkyoku-sukatto
    "UCjy5fWoigvtCfduJDJ3jTbg",   # L shakai-no-naze
    "UClHVEGr-4pG0CDW_YUKJ26g",   # H kokoro-kazoku
    "UCxBOdUsVT8g8WnpvJ8SdjyQ",   # I sengoku-uragawa
    "UC6IkfxpGTksDdzG3ENYbVdg",   # J teinengo-fuufu
    "UCqXxSE88mHQiZMvzCdlmk3w",   # Lane-N senior_kurashi60
    "UCnwgkB18gTTON1YXNQvxsbg",   # Lane-O 人生のつづき
    "UC-03gNBRs14lZHus7TiKofA",   # M teinengo-anaba
}
