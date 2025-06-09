import math
from app.api import bp
from flask import request, jsonify
from app import db
from app.constants import (
    NUM_POSTS_PER_PAGE,
    PaginationType,
    PostSearchCondition,
)
from flask_login import current_user, login_required
from app.models import QueryUtility, Post
from datetime import datetime
from flask_babel import _

from app.translate import translate_text


@bp.route("/posts")
@login_required
def posts():

    # Input
    search_condition = request.args.get("search_condition", PostSearchCondition.ALL)
    pagination_type = request.args.get("pagination_type", PaginationType.OFFSET)
    flag_pagination_info = request.args.get("flag_pagination_info", True, type=bool)
    per_page = request.args.get("per_page", NUM_POSTS_PER_PAGE, type=int)
    user_id = request.args.get("user_id")

    # Output
    serialized_posts = None
    pagination_info = {
        # keyset
        "has_more": None,
        "next_cursor": None,
        # offset
        "total_records": None,
        "total_pages": None,
    }

    # Get base query
    match search_condition:
        case PostSearchCondition.ALL:
            base_query = Post.query_all_posts()
        case PostSearchCondition.CURRENT_USER_AND_FOLLOWING:
            base_query = Post.query_posts_of_user_and_following(current_user.id)
        case PostSearchCondition.USER:
            if not user_id:
                return jsonify({"error": "Query param 'user_id' is missing"}), 400
            base_query = Post.query_posts_of_user(user_id)
        case _:
            return jsonify({"error": "Invalid query type"}), 400

    # Pagination approach
    match pagination_type:
        case PaginationType.OFFSET:
            # Input
            page = request.args.get("page", 1, type=int)  # TODO test case not number

            # Get pagination query (by offset)
            query = QueryUtility.pagination_by_offset(base_query, per_page, page)

            # Execute query
            posts = db.session.scalars(query).all()

            # Serialize posts to dictionaries
            serialized_posts = [p.to_dict() for p in posts]

            if flag_pagination_info:
                total_records = QueryUtility.count_total(base_query)
                pagination_info["total_records"] = total_records
                pagination_info["total_pages"] = math.ceil(total_records / per_page)
        case PaginationType.KEYSET:
            # Check input
            cursor_timestamp_str = request.args.get("cursor_timestamp")
            cursor_id = request.args.get("cursor_id")
            cursor_timestamp = None
            if cursor_timestamp_str:
                try:
                    cursor_timestamp = datetime.fromisoformat(cursor_timestamp_str)
                except ValueError:
                    return jsonify({"error": "Invalid timestamp format"}), 400

            # Get pagination query (by keyset)
            query = QueryUtility.pagination_by_keyset(
                base_query, per_page + 1, cursor_timestamp, cursor_id
            )

            # Execute query
            posts = db.session.scalars(query).all()

            # Check next cursor
            pagination_info["has_more"] = len(posts) > per_page
            if pagination_info["has_more"]:
                pagination_info["next_cursor"] = {
                    "cursor_timestamp": posts[per_page - 1].timestamp.isoformat(),
                    "cursor_id": posts[per_page - 1].id,
                }

            # Serialize posts to dictionaries
            posts_to_return = posts[:per_page]
            serialized_posts = [p.to_dict() for p in posts_to_return]
        case _:
            return jsonify({"error": "Invalid pagination type"}), 400

    return jsonify(
        {
            "posts": serialized_posts,
            "pagination_info": pagination_info if flag_pagination_info else None,
        }
    )


@bp.route("/translate", methods=["POST"])
@login_required
def translate():
    data = request.get_json()
    text = translate_text(
        data["text"], data["source_language"], data["target_language"]
    )
    return {"text": text}
