import uuid

def generate_unique_post_img_id(file_name: str) -> str:
    unique_suffix = str(uuid.uuid4())
    return f"{file_name}-@-{unique_suffix}"

def extract_file_name_from_post_img_id(post_img_id: str) -> str:
    return post_img_id.rsplit('-@-', 1)[0]

def remove_all_side_quotes(s):
    # 양 끝 문자가 따옴표(') 또는 쌍따옴표(")인지 확인하고, 해당되면 제거한 문자열을 반환
    if s.startswith(("'", '"')) and s.endswith(("'", '"')):
        return s[1:-1]
    return s


def remove_quotes(s):
    # 시작 부분에서 따옴표 또는 쌍따옴표 제거
    if s.startswith(("'", '"')):
        s = s[1:]
    # 끝 부분에서 따옴표 또는 쌍따옴표 제거
    if s.endswith(("'", '"')):
        s = s[:-1]
    return s