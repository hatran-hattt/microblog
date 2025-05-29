class LengthValidation:
    USER_NAME_MIN_LENGTH = 3
    USER_NAME_MAX_LENGTH = 80


NUM_POSTS_PER_PAGE = 10


class PostSearchCondition:
    ALL = "all"
    CURRENT_USER_AND_FOLLOWING = "current_user_and_following"
    USER = "user"


class PaginationType:
    OFFSET = "offset"
    KEYSET = "keyset"
