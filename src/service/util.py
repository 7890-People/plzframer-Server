import uuid

def generate_unique_post_img_id(file_name: str) -> str:
    unique_suffix = str(uuid.uuid4())
    return f"{file_name}-@-{unique_suffix}"

def extract_file_name_from_post_img_id(post_img_id: str) -> str:
    return post_img_id.rsplit('-@-', 1)[0]

def remove_all_side_quotes(s):
    # �� �� ���ڰ� ����ǥ(') �Ǵ� �ֵ���ǥ(")���� Ȯ���ϰ�, �ش�Ǹ� ������ ���ڿ��� ��ȯ
    if s.startswith(("'", '"')) and s.endswith(("'", '"')):
        return s[1:-1]
    return s


def remove_quotes(s):
    # ���� �κп��� ����ǥ �Ǵ� �ֵ���ǥ ����
    if s.startswith(("'", '"')):
        s = s[1:]
    # �� �κп��� ����ǥ �Ǵ� �ֵ���ǥ ����
    if s.endswith(("'", '"')):
        s = s[:-1]
    return s