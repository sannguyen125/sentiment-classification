"""CSS selectors for dienmayxanh.com, from the DOM survey on 2026-09-30.
Sample HTML: data/raw/html_cache/_survey/{survey_0,pag_0,pag_1star,cate_may-giat}.html

Review page: {product_url}/danh-gia
  - 404 when the product has no reviews / is discontinued.
  - <title> starts with "{N} đánh giá ..." -> total number of text reviews.
  - 20 reviews per page. Only reviews with text are listed; the star-bar
    percentages at the top also count silent ratings, so they are NOT used.
  - No posting date is shown for a review (only "Đã dùng khoảng X").
"""

# --- review list ---
REVIEW_ITEM = "ul#scrollList > li.par"      # one review; id="r-{rating_id}"
REVIEW_TEXT = ".cmt-content p.cmt-txt"      # review text
STAR_ON = ".cmt-top-star i.iconcmt-starbuy"  # count of filled stars = rating 1..5
VERIFIED = ".cmt-top .confirm-buy"           # "Đã mua tại ĐMX" badge
USED_FOR = ".cmt-command .cmtd"              # "Đã dùng khoảng 3 tháng"
# Personal data, never stored: stripped from HTML before it is cached
PERSONAL = [".cmt-top-name", ".cmt-img"]     # reviewer name, reviewer photos
# Shop response: div.support ("Bộ phận bảo hành đã liên hệ hỗ trợ ngày ...")
#   is a sibling of .cmt-content, so reading only REVIEW_TEXT excludes it.

PRODUCT_ID = ".wrap_rating[data-objectid]"   # attr data-objectid = DMX product id

# --- rating summary at top of review page ---
# NOTE: average + bars count "khách hài lòng" = 5★ raters AND buyers who never rated
# (since 01/2022), so they are inflated; the text-review distribution is counted separately.
PAGE_AVG = ".point-average-score"            # "4.9"
RATE_BARS = "ul.rate-list > li"              # text like "5 99.7%"

# --- star filter (click, the page loads results itself) ---
STAR_FILTER_ITEMS = "ul.filter-list > li"    # index 0 = "Tất cả", 1..5 = 5★..1★
# ul.filter-list[data-star] does NOT change on click. After a filter/page click we
# only *observe* the response the page itself fires (URL contains this marker);
# the crawler never calls it directly.
LIST_RESPONSE_MARKER = "/comment/PagingAllRating"

# --- pagination (click, the page loads results itself) ---
PAGINATION = ".boxrate .pagcomment"
PAGE_LINK = '.boxrate .pagcomment a[title="trang {n}"]'  # href="javascript:ratingCmtList(n)"

# --- category listing page: /{category} ---
CATE_ITEM = "ul.listproduct > li.item"
CATE_LINK = "a.main-contain"                 # href="/{category}/{slug}?..."
CATE_META = ".rating_Compare"                # "★ 4.9 • Đã bán 41,8k"
CATE_VOTE = ".vote-txt b"                    # "4.9" (same inflated average as PAGE_AVG)
CATE_VIEW_MORE = ".view-more a"              # "Xem thêm N ..." button
