from flask import Blueprint, request, jsonify, abort

from main.auth import jwt_required
from main.constants import (BAD_REQUEST, UNAUTHORIZED, NOT_FOUND, NO_CONTENT)
from main.models.category import CategoryModel
from main.models.item import ItemModel
from main.models.user import UserModel
from main.schemas.item import item_input_schema, item_output_schema, items_output_schema
from main.schemas.query import query_validation_schema
from main.controllers.errors import (BadRequest, Forbidden, NotFound)


items = Blueprint('items', __name__, url_prefix='/items')


@items.route('/', methods=['GET'])
def get_items():
    validate = query_validation_schema.load(request.args)
    if len(validate.errors) > 0:
        return BadRequest(message=validate.errors).to_json()
    query = ItemModel.query
    if validate.data.get('name') is not None:
        query = query.filter_by(name=validate.data.get('name'))
    if validate.data.get('category_id') is not None:
        query = query.filter_by(category_id=validate.data.get('category_id'))
    page = validate.data.get('page')
    per_page = validate.data.get('per_page')
    results = query.order_by(ItemModel.created_at.desc()) \
        .paginate(page, per_page, error_out=False)
    return jsonify({
        'items': items_output_schema.dump(results.items).data,
        'pages': results.pages,
        'total': results.total
    })


@items.route('/<int:item_id>', methods=['GET'])
def get_item_with_id(item_id):
    result = ItemModel.query.get(item_id)
    if not result:
        return NotFound(message='item with id {} does not exist'.format(item_id)).to_json()
    return jsonify(item_output_schema.dump(result).data)


@items.route('/', methods=['POST'])
@jwt_required
def post_item(user_id):
    data = request.get_json()
    validate = item_input_schema.load(data)
    if len(validate.errors) > 0:
        return BadRequest(message=validate.errors).to_json()
    user = UserModel.query.get(user_id)
    category_id = data.get('category_id')
    category = None
    if category_id:
        category = CategoryModel.query.get(category_id)
        if category and category.creator_id != user_id:
            return Forbidden(message='unauthorized to assign item to category {}'
                  .format(category.name)).to_json()
    item = ItemModel(creator=user, category=category, **data)
    item.save_to_db()
    return jsonify({'message': 'item with name {} has been successfully created'.format(data.get('name'))})


@items.route('/<int:item_id>', methods=['PUT'])
@jwt_required
def update_item(user_id, item_id):
    data = request.get_json()
    validate = item_input_schema.load(data)
    if len(validate.errors) > 0:
        return BadRequest(message=validate.errors).to_json()
    item = ItemModel.query.get(item_id)
    if item:  # if item exists
        if item.creator_id != user_id:
            return Forbidden(message='Unauthorized to modify the content of this item').to_json()
        category_id = data.get('category_id')
        if category_id:
            category = CategoryModel.query.get(category_id)
            if category:
                if category.creator_id != user_id:
                    return Forbidden(message='Unauthorized to change the category of this item').to_json()
            else:
                return NotFound(message='category with id {} does not exist'.format(category_id)).to_json()
        for key, val in data.items():
            setattr(item, key, val)
    else:
        item = ItemModel(**data)
    item.save_to_db()
    return '', NO_CONTENT


@items.route('/<int:item_id>', methods=['DELETE'])
@jwt_required
def delete_item(user_id, item_id):
    item = ItemModel.query.get(item_id)
    if not item:
        return NotFound(message='item with id {} does not exist'.format(item_id)).to_json()
    if item.creator_id != user_id:
        return Forbidden().to_json()
    item.delete_from_db()
    return '', NO_CONTENT
